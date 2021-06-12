from pyupbit2 import *
import time
import datetime
import requests
import pandas as pd
import telegram

# Global variables
VERSION = "21.06.12.52"     # 미사용 함수, 변수 삭제, main 구문 함수화
# 잔고
startBalance = hourlyBalance = totalBalance = balanceBackup = balance = 0
# 매매 횟수
num_buy = num_sell = num_buy_total = num_sell_total = 0
# 종목
tkr_num = 10
tkr_buy = ["KRW-BTC", "KRW-ETH", "KRW-ADA", "KRW-XRP", "KRW-DOGE", "KRW-DOT", "KRW-BCH", "KRW-LTC", "KRW-LINK", "KRW-ETC"]     
# RSI
rsi_intv = 5
rsi14 = rsi14_back = [0]*tkr_num
rsr_l_min = [100]*tkr_num
rsr_h_max = [0]*tkr_num
rsr_l_sum = [300]*tkr_num
rsr_h_sum = [700]*tkr_num
rsr_l_avg = [30]*tkr_num
rsr_h_avg = [70]*tkr_num
f_rsi_l = f_rsi_h = f_rsi_30 = f_rsi_70 = rsr_l_chk = rsr_h_chk = [0]*tkr_num
rsr_l_cnt = rsr_l_cnt_d = rsr_h_cnt = rsr_h_cnt_d = [10]*tkr_num
# 시간
f_start = 0
time_backup = min_backup = last_rx_time = -1


# Keys
access = "UfxFeckqIxoheTgBcgN3KNa6vtP98WEWlyjDmHx6" 
secret = "NknKBgNg1cLnh8I4KYH2byIzvbDmx7171lrbxfLL"
upbit = Upbit(access, secret)
token = "1814838763:AAGNuB_LWtq8zJMHuezB-vsSI8C4b9X9QLk"
chat_id = 1883488213
bot = telegram.Bot(token)

# Functions
def send(str):
    bot.sendMessage(chat_id,str)

def send_start_message():
    txt = "==================================\n"
    txt+= "autotrade start (ver."+VERSION+"))\n"
    txt+= str(datetime.datetime.now())+"\n"
    txt+= "=================================="
    send(txt)

def get_current_price(ticker):
    # 현재가 조회
    return get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def get_krw():
    # 잔고 조회
    balances = upbit.get_balances()
    print(balances)
    for b in balances:
        if b['currency'] == "KRW":
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0

def get_totalKRW():
    # 잔고 조회
    balances = upbit.get_balances()
    krw = 0
    for b in balances:
        if b['currency'] == "KRW":
            if b['balance'] is not None:
                krw += float(b['balance'])
        elif float(b['avg_buy_price']) > 0:
            if b['balance'] is not None:
                krw += float(b['balance']) * get_current_price("KRW-"+b['currency'])
    return krw

def get_balance(tkr, sel):
    # 잔고 조회
    coin = tkr[4:]
    balances = upbit.get_balances()
    ret = 0
    for b in balances:
        if b['currency'] == coin:
            if b['balance'] is not None and float(b['avg_buy_price']) > 0:
                ret = float(b['balance'])
            else:
                ret = 0
    if sel == "COIN":
        return ret
    elif sel == "KRW":
        return ret * get_current_price("KRW-"+coin)
    else:
        return 0

def get_avg_buy_price(tkr):
    # 잔고 조회
    coin = tkr[4:]
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == coin:
            if b['balance'] is not None:
                return float(b['avg_buy_price'])
            else:
                return 1
    return 1

def buy(tkr, balance):
    buy_result = upbit.buy_market_order(tkr, balance*0.999)
    if buy_result != None:
        return True
    else:
        return False

def sell(tkr, balance):
    tot_c = get_balance(tkr,"COIN")
    tot_k = get_balance(tkr,"KRW")
    if balance == 0:
        sell_result = upbit.sell_market_order(tkr, tot_c)
    else:
        num_c = tot_c * (balance/tot_k)
        sell_result = upbit.sell_market_order(tkr, num_c)

    if sell_result != None:
        return True
    else:
        return False

def sell_not_in():
    # 미관리 종목 전량 매도
    balances = upbit.get_balances()
    global num_sell
    time.sleep(0.1)
    for b in balances:
        if b['currency'] != 'KRW' and float(b['avg_buy_price']) > 0:
            tkr = "KRW-"+b['currency']
            if tkr not in tkr_buy:
                if get_balance(tkr,"KRW") > 5000:
                    sell(tkr)
                    num_sell += 1
                time.sleep(0.1)

def get_rsi14(symbol, candle):
    url = "https://api.upbit.com/v1/candles/minutes/"+str(candle)
    querystring = {"market":symbol,"count":"500"}
    response = requests.request("GET", url, params=querystring)
    data = response.json()
    df = pd.DataFrame(data)
    df=df.reindex(index=df.index[::-1]).reset_index()
    df['close']=df["trade_price"]
    def rsi(ohlc: pd.DataFrame, period: int = 14):
        ohlc["close"] = ohlc["close"]
        delta = ohlc["close"].diff()
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        _gain = up.ewm(com=(period - 1), min_periods=period).mean()
        _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
        RS = _gain / _loss
        return pd.Series(100 - (100 / (1 + RS)), name="RSI")
    rsi = rsi(df, 14).iloc[-1]
    time.sleep(0.5)
    return rsi

def check_rsi(i):
    global rsi14, f_rsi_l, f_rsi_h
    rsi14[i] = get_rsi14(tkr_buy[i], rsi_intv)
    # rsi 하방 check
    if rsi14[i] < rsr_l_avg[i]:
        f_rsi_l[i] = 1
    if f_rsi_l[i] == 1 and rsi14[i] > rsr_l_avg[i]:
        f_rsi_l[i] = 2
    # rsi 상방 check
    if rsi14[i] > rsr_h_avg[i]:
        f_rsi_h[i] = 1
    if f_rsi_h[i] == 1 and rsi14[i] < rsr_h_avg[i]:
        f_rsi_h[i] = 2

def calc_rsi_avg(i):
    global rsr_h_chk, rsr_h_max, rsr_h_sum, rsr_h_cnt, rsr_h_avg
    global rsr_l_chk, rsr_l_min, rsr_l_sum, rsr_l_cnt, rsr_l_avg
    if rsi14[i] > 60:
        rsr_h_chk[i] = 1
        if rsi14[i] > rsr_h_max[i]:
            rsr_h_max[i] = rsi14[i]
    else:
        if rsr_h_chk[i] == 1:
            rsr_h_sum[i] += rsr_h_max[i]
            rsr_h_cnt[i] += 1
            rsr_h_cnt_d[i] += 1
            rsr_h_avg[i] = rsr_h_sum[i] / rsr_h_cnt[i]
            rsr_h_max[i] = 0
            rsr_h_chk[i] = 0
    if rsi14[i] < 40:
        rsr_l_chk[i] = 1
        if rsi14[i] < rsr_l_min[i]:
            rsr_l_min[i] = rsi14[i]
    else:
        if rsr_l_chk[i] == 1:
            rsr_l_sum[i] += rsr_l_min[i]
            rsr_l_cnt[i] += 1
            rsr_l_cnt_d[i] += 1
            rsr_l_avg[i] = rsr_l_sum[i] / rsr_l_cnt[i]
            rsr_l_min[i] = 100
            rsr_l_chk[i] = 0
		
def trade(i):
    global num_buy, num_sell, f_rsi_l, f_rsi_h
    avg_buy = get_avg_buy_price(tkr_buy[i])
    current = get_current_price(tkr_buy[i])
    # 매수 : rsi low 미만 -> 초과 시
    if f_rsi_l[i] == 2:
        krw = get_krw()
        tkr_balance = get_balance(tkr_buy[i], "KRW")
        total_krw = get_totalKRW()
        if tkr_balance < (total_krw/tkr_num) and krw > 5000:
            current = get_current_price(tkr_buy[i])
            if krw - 10000 < 5000:
                buy(tkr_buy[i], krw)
            else:
                buy(tkr_buy[i], 10000)
            num_buy += 1
            send(tkr_buy[i]+" 매수 (rsi: "+str(round(rsi14[i]))+", 가격: "+str(round(current))+")")
        f_rsi_l[i] = 0
    # 매도 : rsi 70 초과 -> 미만 시
    if f_rsi_h[i] == 2:
        krw = get_krw()
        tkr_balance = get_balance(tkr_buy[i], "KRW")
        total_krw = get_totalKRW()
        if tkr_balance > 5000:
            current = get_current_price(tkr_buy[i])
            if tkr_balance - 10000 < 5000:
                sell(tkr_buy[i], 0)
            else:
                sell(tkr_buy[i], 10000)
            num_sell += 1
            send(tkr_buy[i]+" 매도 (rsi: "+str(round(rsi14[i]))+", 가격: "+str(round(current))+")")
        f_rsi_h[i] = 0
    # 손절 : -2% 미만 시 전량 매도
    if (current-avg_buy)/avg_buy < -0.02:
        sell(tkr_buy[i], 0)
        num_sell += 1
        send(tkr_buy[i]+" 손절("+str(round((current-avg_buy)/avg_buy, 2))+")")

def reset_newday():
    global num_buy_total, num_sell_total, startBalance, hourlyBalance
    global rsr_l_sum, rsr_l_cnt, rsr_l_cnt_d, rsr_l_avg, rsr_h_sum, rsr_h_cnt, rsr_h_cnt_d, rsr_h_avg
    num_buy_total = num_sell_total = 0
    for i in range(0,tkr_num):
        rsr_l_sum[i] = 30 + rsr_l_avg[i] * rsr_l_cnt_d[i]
        rsr_l_cnt[i] = rsr_l_cnt_d[i] + 1
        rsr_l_cnt_d[i] = 0
        rsr_l_avg[i] = rsr_l_sum[i] / rsr_l_cnt[i]
        rsr_h_sum[i] = 70 + rsr_h_avg[i] * rsr_h_cnt_d[i]
        rsr_h_cnt[i] = rsr_h_cnt_d[i] + 1
        rsr_h_cnt_d[i] = 0
        rsr_h_avg[i] = rsr_h_sum[i] / rsr_h_cnt[i]
    # 미관리 종목 전량 매도
    sell_not_in()
    # 잔고 Update
    startBalance = hourlyBalance = get_totalKRW()

def send_hourly_report(req):
    global rsi14, hourlyBalance, num_buy_total, num_sell_total, num_buy, num_sell
    # 수익 계산
    num_buy_total += num_buy
    num_sell_total += num_sell
    curBalance = get_totalKRW()
    balChange_hr = curBalance - hourlyBalance
    balChngPercent_hr = balChange_hr / hourlyBalance * 100
    balChange_d = curBalance - startBalance
    balChngPercent_d = balChange_d / startBalance * 100
    # 결과 송신
    if req == 1:
        txt = "=== Hourly Report ===\n"
    elif req == 0:
        txt = "=== Current Report ===\n"
    txt+= " - 현재 잔고  : "+str(round(curBalance))+"원\n"
    txt+= " - 매수(시간) : "+str(num_buy)+"회, 매도(시간) : "+str(num_sell)+"회\n"
    txt+= " - 매수(금일) : "+str(num_buy_total)+"회, 매도(금일) : "+str(num_sell_total)+"회\n"
    txt+= " - 수익(시간) : "+str(round(balChange_hr))+"원 ("+str(round(balChngPercent_hr, 2))+"%)\n"
    txt+= " - 수익(금일) : "+str(round(balChange_d))+"원 ("+str(round(balChngPercent_d, 2))+"%)"
    send(txt)
    if req == 1:
        hourlyBalance = curBalance
        num_buy = num_sell = 0
    elif req == 0:
        num_buy_total -= num_buy
        num_sell_total -= num_sell
    # RSI 값 송신
    txt = "=== RSI14 Value ===\n"
    for i in range(0,tkr_num):
        if rsi14[i] == 0:
            rsi14[i] = get_rsi14(tkr_buy[i], rsi_intv)
        txt += tkr_buy[i]+" : "+str(round(rsr_h_avg[i],1))+"/"+str(round(rsi14[i],1))+"/"+str(round(rsr_l_avg[i],1))+"\n"
    send(txt)

def check_message():
    global last_rx_time
    latest = bot.getUpdates()[-1].message
    if latest.date != last_rx_time:
        if latest.text == "report":
            send_hourly_report(0)
        last_rx_time = latest.date

