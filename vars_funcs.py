from pyupbit2 import *
import time
import datetime
import requests
import pandas as pd
import telegram
import sys
from telegram.ext import Updater, MessageHandler, Filters

# Global variables
VERSION = "21.07.17.81"     # 
# 잔고
startBalance = 0; hourlyBalance = 0; totalBalance = 0; balanceBackup = 0; balance = 0
# 매매 횟수
num_buy = 0; num_sell = 0; num_buy_total = 0; num_sell_total = 0
# 종목
max_num = 110
tkr_num = 10
tkr_all = get_tickers(fiat = "KRW")
tkr_buy = ["-"]*max_num
tkr_default = ["KRW-BTC", "KRW-ETH", "KRW-ADA", "KRW-XRP", "KRW-DOGE", "KRW-DOT", "KRW-BCH", "KRW-LTC", "KRW-LINK", "KRW-ETC"]
for i in range(0, tkr_num):
    tkr_buy[i] = tkr_default[i]
# RSI
rsi_intv = 10
rsi14 = [0]*max_num
rsi_l_limit = [30]*max_num; 
rsi_h_limit = [70]*max_num;
f_rsi_under = [0]*max_num;
f_rsi_over = [0]*max_num;
rsi_high = 60
rsi_low = 40
skip_trade = [0]*max_num
# 기준값
unit_trade_price = 25000
stop_loss = 0.005
stop_trade = 0
restart = 0
chatbot_chk = 0
# 챗봇 confirm
confirm_sell = 0; confirm_quit = 0; confirm_stop = 0; confirm_start = 0; confirm_restart = 0
trade_chk = 0
# 시간
f_start = 0; time_backup = -1; min_backup = -1; start_time = 0; trade_intv = 5
# Keys
access = "UfxFeckqIxoheTgBcgN3KNa6vtP98WEWlyjDmHx6" 
secret = "NknKBgNg1cLnh8I4KYH2byIzvbDmx7171lrbxfLL"
upbit = Upbit(access, secret)
token = "1814838763:AAGNuB_LWtq8zJMHuezB-vsSI8C4b9X9QLk"
chat_id = 1883488213
bot = telegram.Bot(token)
backup_path = "../parameter_backup.txt"

# Functions
def check_chatbot(cmd):
    global chatbot_chk
    if cmd == "set":
        chatbot_chk += 1
    if cmd == "clear":
        chatbot_chk = 0
    return chatbot_chk

def send(str):
    if chatbot_chk < 10:
        bot.sendMessage(chat_id,str,timeout=3)

def get_current_price(ticker):
    # 현재가 조회
    return get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def get_krw():
    # 잔고 조회
    balances = upbit.get_balances()
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
    global num_sell
    balances = upbit.get_balances()
    time.sleep(0.1)
    for b in balances:
        if b['currency'] != 'KRW' and float(b['avg_buy_price']) > 0:
            tkr = "KRW-"+b['currency']
            if tkr not in tkr_buy:
                if get_balance(tkr,"KRW") > 5000:
                    sell(tkr, 0)
                    num_sell += 1
                time.sleep(0.1)

def sell_all():
    # 전량 매도
    global num_sell
    balances = upbit.get_balances()
    time.sleep(0.1)
    for b in balances:
        if b['currency'] != 'KRW' and float(b['avg_buy_price']) > 0:
            tkr = "KRW-"+b['currency']
            if get_balance(tkr,"KRW") > 5000:
                sell(tkr, 0)
                num_sell += 1
            time.sleep(0.1)

def is_trade_cond(now):
    global min_backup
    if stop_trade == 1:
        return False
    if min_backup != now.minute and now.minute % trade_intv == 0:
        min_backup = now.minute
        return True
    else:
        return False

def get_rsi14(symbol, candle):
    url = "https://api.upbit.com/v1/candles/minutes/"+str(candle)
    querystring = {"market":symbol,"count":"200"}
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

def set_rsi_h_l_limit(i):
    global rsi14, rsi_l_limit, rsi_h_limit, rsi_high, rsi_low

    if rsi14[i] < rsi_low:
        if rsi14[i] < rsi_l_limit[i]:
            rsi_l_limit[i] = ((int)((rsi14[i]/5)+1)) * 5
    else:
        rsi_l_limit[i] = rsi_low

    if rsi14[i] > rsi_high:
        if rsi14[i] > rsi_h_limit[i]:
            rsi_h_limit[i] = ((int)(rsi14[i]/5)) * 5
    else:
        rsi_h_limit[i] = rsi_high
    time.sleep(0.01)

def check_rsi(i):
    global rsi14, f_rsi_under, f_rsi_over, skip_trade
    rsi14[i] = get_rsi14(tkr_buy[i], rsi_intv)
    set_rsi_h_l_limit(i)

    # rsi 하방 check
    if f_rsi_under[i] == 0 and rsi14[i] < rsi_low:
        f_rsi_under[i] = 1
    elif f_rsi_under[i] == 1 and rsi_l_limit[i] < rsi14[i] < rsi_low:
        f_rsi_under[i] = 2
    elif rsi14[i] >= rsi_low:
        f_rsi_under[i] = 0
        skip_trade[i] = 0
        rsi_l_limit[i] = rsi_low

    # rsi 상방 check
    if f_rsi_over[i] == 0 and rsi14[i] > rsi_high:
        f_rsi_over[i] = 1
    elif f_rsi_over[i] == 1 and rsi_high < rsi14[i] < rsi_h_limit[i]:
        f_rsi_over[i] = 2
    elif rsi14[i] <= rsi_high:
        f_rsi_over[i] = 0
        skip_trade[i] = 0
        rsi_h_limit[i] = rsi_high
    time.sleep(0.01)
		
def trade(i):
    global num_buy, num_sell, f_rsi_under, f_rsi_over, trade_chk, skip_trade
    avg_buy = get_avg_buy_price(tkr_buy[i])
    current = get_current_price(tkr_buy[i])
    # 매수 : rsi low 미만 -> 초과 시
    if f_rsi_under[i] == 2 and skip_trade[i] == 0:
        krw = get_krw()
        tkr_balance = get_balance(tkr_buy[i], "KRW")
        total_krw = get_totalKRW()
        #if tkr_balance < (total_krw/20) and krw > 5000:
        if tkr_balance < (total_krw/tkr_num) and krw > 5000:
            current = get_current_price(tkr_buy[i])
            if krw - unit_trade_price < 5000:
                buy(tkr_buy[i], krw)
            else:
                buy(tkr_buy[i], unit_trade_price)
            num_buy += 1
            txt = tkr_buy[i]+" 매수(price : "+str(round(current))+")\n"
            txt+= "rsi : "+str(round(rsi_h_limit[i]))+"/"+str(round(rsi_high))+"/"+str(round(rsi14[i]))+"/"+str(round(rsi_low))+"/"+str(round(rsi_l_limit[i]))
            send(txt)
        f_rsi_under[i] = 0
        skip_trade[i] = 1
    # 매도 : rsi 70 초과 -> 미만 시
    if f_rsi_over[i] == 2 and skip_trade[i] == 0:
        krw = get_krw()
        tkr_balance = get_balance(tkr_buy[i], "KRW")
        total_krw = get_totalKRW()
        if tkr_balance > 5000:
            current = get_current_price(tkr_buy[i])
            if tkr_balance - unit_trade_price < 5000:
                sell(tkr_buy[i], 0)
            else:
                sell(tkr_buy[i], unit_trade_price)
            num_sell += 1
            txt = tkr_buy[i]+" 매도\n"
            txt+= "현재가 : "+str(current)+"/평단가 : "+str(avg_buy)+"("+str(round(((current-avg_buy)/avg_buy)*100, 2))+"%)\n"
            txt+= "rsi : "+str(round(rsi_h_limit[i]))+"/"+str(round(rsi_high))+"/"+str(round(rsi14[i]))+"/"+str(round(rsi_low))+"/"+str(round(rsi_l_limit[i]))
            send(txt)
        f_rsi_over[i] = 0
        skip_trade[i] = 1
    # 손절 : -2% 미만 시 전량 매도
    if (current-avg_buy)/avg_buy < -stop_loss:
        sell(tkr_buy[i], 0)
        num_sell += 1
        txt = tkr_buy[i]+" 손절\n"
        txt+= "현재가 : "+str(current)+"/평단가 : "+str(avg_buy)+"("+str(round(((current-avg_buy)/avg_buy)*100, 2))+"%)\n"
        txt+= "rsi : "+str(round(rsi_h_limit[i]))+"/"+str(round(rsi_high))+"/"+str(round(rsi14[i]))+"/"+str(round(rsi_low))+"/"+str(round(rsi_l_limit[i]))
        send(txt)
    if trade_chk == 1 and i == tkr_num-1:
        send("trade running")
    time.sleep(0.01)

def do_trade():
    for i in range(0, tkr_num):
        check_rsi(i)
        trade(i)

def reset_newday():
    global num_buy_total, num_sell_total, startBalance, hourlyBalance
    global rsi_l_limit, rsi_h_limit
    num_buy_total = num_sell_total = 0
    # 미관리 종목 전량 매도
    sell_not_in()
    # 잔고 Update
    startBalance = hourlyBalance = get_totalKRW()

def send_start_message():
    txt = "==================================\n"
    txt+= "autotrade start (ver."+VERSION+"))\n"
    txt+= str(start_time)+"\n"
    txt+= "=================================="
    send(txt)

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
    r_time = datetime.datetime.now() - start_time
    # 결과 송신
    if req == 1:
        txt = "========== Hourly Report ==========\n"
    elif req == 0:
        txt = "========== Current Report ==========\n"
    txt+= " - 현재 잔고  : "+str(round(curBalance))+"원\n"
    txt+= " - 매수(시간) : "+str(num_buy)+"회, 매도(시간) : "+str(num_sell)+"회\n"
    txt+= " - 매수(금일) : "+str(num_buy_total)+"회, 매도(금일) : "+str(num_sell_total)+"회\n"
    txt+= " - 수익(시간) : "+str(round(balChange_hr))+"원 ("+str(round(balChngPercent_hr, 2))+"%)\n"
    txt+= " - 수익(금일) : "+str(round(balChange_d))+"원 ("+str(round(balChngPercent_d, 2))+"%)\n"
    txt+= " - Running  : "+str(r_time)+"\n"
    if req == 1:
        hourlyBalance = curBalance
        num_buy = num_sell = 0
    elif req == 0:
        num_buy_total -= num_buy
        num_sell_total -= num_sell

    # RSI 값 송신
    txt+= "========== RSI14 Value ==========\n"
    for i in range(0,tkr_num):
        if rsi14[i] == 0:
            rsi14[i] = get_rsi14(tkr_buy[i], rsi_intv)
            set_rsi_h_l_limit(i)
        txt += tkr_buy[i]+" : "+str(round(rsi_h_limit[i],1))+"/"+str(round(rsi_high,1))+"/"+str(round(rsi14[i],1))+"/"+str(round(rsi_low,1))+"/"+str(round(rsi_l_limit[i],1))+"\n"
    send(txt)


def restore():
    global unit_trade_price, stop_loss, trade_intv, rsi_intv, rsi_high, rsi_low
    global tkr_num, tkr_buy
    f = open(backup_path, 'r')
    unit_trade_price = int(f.readline())
    trade_intv = int(f.readline())
    rsi_intv = int(f.readline())
    stop_loss = float(f.readline())
    rsi_high = float(f.readline())
    rsi_low = float(f.readline())
    tmp = f.readline()
    if tmp != '':
        tkr_num = int(tmp)
    for i in range(0,tkr_num):
        tmp = f.readline()
        if len(tmp) > 3:
            tkr_buy[i] = tmp[0:-1]
    f.close()
    txt = "Parameters are restored\n"
    txt+= "  1: unit_trade_price : "+str(unit_trade_price)+"\n"
    txt+= "  2: trade_intv : "+str(trade_intv)+"\n"
    txt+= "  3: rsi_intv : "+str(rsi_intv)+"\n"
    txt+= "  4: stop_loss : "+str(stop_loss)+"\n"
    txt+= "  5: rsi_high : "+str(rsi_high)+"\n"
    txt+= "  6: rsi_low : "+str(rsi_low)+"\n"
    txt+= "  tkr_num : "+str(tkr_num)+"\n"
    txt+= "  tkr_buy : "+str(tkr_buy[0:tkr_num])+"\n"
    send(txt)

def backup():
    global unit_trade_price, stop_loss, trade_intv, rsi_intv, rsi_high, rsi_low
    global tkr_num, tkr_buy
    f = open(backup_path, 'w')
    f.write(str(unit_trade_price)+"\n")
    f.write(str(trade_intv)+"\n")
    f.write(str(rsi_intv)+"\n")
    f.write(str(stop_loss)+"\n")
    f.write(str(rsi_high)+"\n")
    f.write(str(rsi_low)+"\n")
    f.write(str(tkr_num)+"\n")
    for i in range(0, tkr_num):
        f.write(tkr_buy[i]+"\n")
    f.close()
    send("Backed up parameters")

def check_restart():
    global restart
    if restart == 1:
        restart = 0
        return 1
    else:
        return 0

def chat(update, context):
    global unit_trade_price, stop_loss, confirm_sell, confirm_quit, trade_intv, rsi_intv, rsi_high, rsi_low
    global confirm_stop, confirm_start, stop_trade, confirm_restart, restart, trade_chk, tkr_num, tkr_buy
    new_text = update.message.text
    if new_text != None:
        if new_text[0] == "0":
            send_hourly_report(0)
        elif new_text[0] == "1":
            if len(new_text) < 4:
                send("wrong input")
            elif not('0' <= new_text[3] <= '9'):
                send("wrong input")
            else:
                num = float(new_text[3:])
                if num > 5000:
                    unit_trade_price = int(num)
                    send("unit_trade_price changed : "+str(unit_trade_price))
                    backup()
                else:
                    send("wrong input")
        elif new_text[0] == "2":
            if len(new_text) < 4: 
                send("wrong input")
            elif not('0' <= new_text[3] <= '9'):
                send("wrong input")
            else:
                num = float(new_text[3:])
                if 0 < num < 240:
                    trade_intv = int(num)
                    send("trade_intv changed : "+str(trade_intv))
                    backup()
                else:
                    send("wrong input")
        elif new_text[0] == "3":
            if len(new_text) < 4:
                send("wrong input")
            elif not('0' <= new_text[3] <= '9'):
                send("wrong input")
            else:
                num = float(new_text[3:])
                if 0 < num <= 240:
                    rsi_intv = int(num)
                    send("rsi_intv changed : "+str(rsi_intv))
                    backup()
                else:
                    send("wrong input")
        elif new_text[0] == "4":
            if len(new_text) < 4: 
                send("wrong input")
            elif not('0' <= new_text[3] <= '9'):
                send("wrong input")
            else:
                num = float(new_text[3:])
                if 0 < num < 1:
                    stop_loss = num
                    send("stop_loss changed : "+str(stop_loss))
                    backup()
                else:
                    send("wrong input")
        elif new_text[0] == "5":
            if len(new_text) < 4: 
                send("wrong input")
            elif not('0' <= new_text[3] <= '9'):
                send("wrong input")
            else:
                num = float(new_text[3:])
                if 0 < num < 1 or 50 < num < 90:
                    rsi_high = num
                    send("rsi_high changed : "+str(rsi_high))
                    backup()
                else:
                    send("wrong input")
        elif new_text[0] == "6":
            if len(new_text) < 4: 
                send("wrong input")
            elif not('0' <= new_text[3] <= '9'):
                send("wrong input")
            else:
                num = float(new_text[3:])
                if 0 < num < 1 or 10 < num < 50:
                    rsi_low = num
                    send("rsi_low changed : "+str(rsi_low))
                    backup()
                else:
                    send("wrong input")
        elif new_text[0] == "7":
            if len(new_text) < 4: 
                send("wrong input")
            elif not('A' <= new_text[3] <= 'Z'):
                send("wrong input")
            else:
                tkr = new_text[3:]
                if tkr in tkr_all:
                    tkr_num += 1
                    tkr_buy[tkr_num-1] = tkr
                    send("tkr added : "+tkr_buy[tkr_num-1])
                    backup()
                else:
                    send("wrong input")
        elif new_text[0] == "8":
            if len(new_text) < 4: 
                send("wrong input")
            elif not('A' <= new_text[3] <= 'Z'):
                send("wrong input")
            else:
                tkr = new_text[3:]
                if tkr in tkr_buy:
                    for i in range(0, tkr_num):
                        if tkr == tkr_buy[i]:
                            tkr_buy[i] = tkr_buy[tkr_num-1]
                            break
                    tkr_num -= 1
                    send("tkr deleted : "+tkr)
                    sell_not_in()
                    backup()
                else:
                    send("wrong input")
        elif new_text[0] == "9":
            txt = "1: unit_trade_price : "+str(unit_trade_price)+"\n"
            txt+= "2: trade_intv : "+str(trade_intv)+"\n"
            txt+= "3: rsi_intv : "+str(rsi_intv)+"\n"
            txt+= "4: stop_loss : "+str(stop_loss)+"\n"
            txt+= "5: rsi_high : "+str(rsi_high)+"\n"
            txt+= "6: rsi_low : "+str(rsi_low)+"\n"
            txt+= "tkr_num : "+str(tkr_num)+"\n"
            txt+= "tkr_buy : "+str(tkr_buy[0:tkr_num])+"\n"
            txt+= "stop_trade : "+str(stop_trade)+"\n"
            txt+= "check : "+str(trade_chk)+"\n"
            txt+= "pg version : "+VERSION
            send(txt)
        elif new_text == "check":
            if trade_chk == 0:
                trade_chk = 1
                send("check start")
            elif trade_chk == 1:
                trade_chk = 0
                send("check stop")
        elif new_text == "sell":
            confirm_sell = 1
            txt = "보유종목을 전량 매도합니다.\n"
            txt+= "진행하시겠습니까? (yes/no)"
            send(txt)
        elif new_text == "quit":
            confirm_quit = 1
            txt = "프로그램을 종료합니다.\n"
            txt+= "진행하시겠습니까? (yes/no)"
            send(txt)
        elif new_text == "stop":
            confirm_stop = 1
            txt = "매매를 중단합니다.\n"
            txt+= "진행하시겠습니까? (yes/no)"
            send(txt)
        elif new_text == "start":
            confirm_start = 1
            txt = "매매를 시작합니다.\n"
            txt+= "진행하시겠습니까? (yes/no)"
            send(txt)
        elif new_text == "restart":
            confirm_restart = 1
            txt = "프로그램을 재시작합니다.\n"
            txt+= "진행하시겠습니까? (yes/no)"
            send(txt)
        elif confirm_sell == 1:
            if new_text == "yes":
                confirm_sell = 0
                send("보유종목을 전량 매도합니다.")
                sell_all()
            else:
                confirm_sell = 0
                send("취소합니다.")
        elif confirm_quit == 1:
            if new_text == "yes":
                send("프로그램을 종료합니다.")
                sys.exit()
            else:
                confirm_quit = 0
                send("취소합니다.")
        elif confirm_stop == 1:
            if new_text == "yes":
                send("매매를 중단합니다.")
                stop_trade = 1
            else:
                confirm_stop = 0
                send("취소합니다.")
        elif confirm_start == 1:
            if new_text == "yes":
                send("매매를 중단합니다.")
                stop_trade = 0
            else:
                confirm_start = 0
                send("취소합니다.")
        elif confirm_restart == 1:
            if new_text == "yes":
                send("프로그램을 재시작합니다.")
                restart = 1
            else:
                confirm_restart = 0
                send("취소합니다.")
        else:
            txt = "========== Menu ==========\n"
            txt+= "1, N : unit_trade_price N으로 변경\n"
            txt+= "2, N : trade_intv N으로 변경\n"
            txt+= "3, N : rsi_intv N으로 변경\n"
            txt+= "4, N : stop_loss N으로 변경\n"
            txt+= "5, N : rsi_high N으로 변경\n"
            txt+= "6, N : rsi_low N으로 변경\n"
            txt+= "7, tkr : tkr 종목 추가\n"
            txt+= "8, tkr : tkr 종목 제거\n"
            txt+= "9    : 현재 parameter 값 확인\n"
            txt+= "0    : 현재 상태 출력\n"
            txt+= "sell : 전량 매도\n"
            txt+= "quit : 프로그램 종료\n"
            txt+= "stop : 매매 중지\n"
            txt+= "start : 매매 시작\n"
            txt+= "restart : 프로그램 재시작\n"
            txt+= "그 외 : Menu 출력"
            send(txt)

startBalance = hourlyBalance = get_totalKRW()
start_time = datetime.datetime.now()
updater = Updater(token, use_context=True)
msg_handler = MessageHandler(Filters.text, chat)
updater.dispatcher.add_handler(msg_handler)
