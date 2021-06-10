from pyupbit2 import *
import time
import datetime
import requests
import pandas as pd
#import telegram
from bs4 import BeautifulSoup

# Global variables
VERSION = "21.06.10.45"
startBalance = 0                    # 09시 기준 잔고
hourlyBalance = 0                   # 매시 정각 기준 잔고
totalBalance = 0                    # 현재 보유 원
balanceBackup = 0                   # 이전 보유 원화
balance = 0                         # 종목별 거래금액
num_buy = 0                         # 매수 횟수(시간)
num_sell = 0                        # 매도 횟수(시간)
num_buy_total = 0                   # 매수 횟수(일)
num_sell_total = 0                  # 매도 횟수(일)
tkr_num = 10                        # 매매종목 수
target_price = [0]*tkr_num          # 매매 기준가
buy_price = [0]*tkr_num             # 매수가
open_price = [0]*tkr_num            # 시작가
rsi_intv = 5                        # rsi_intv분봉 rsi 참조
rsi14 = [0]*tkr_num                 # rsi14 값
rsi14_back = [0]*tkr_num            # 이전 rsi14 값
f_rsi_under30 = [0]*tkr_num         # rsi 30미만 감지
f_rsi_over70 = [0]*tkr_num          # rsi 70초과 감지
f_rsi_30 = [0]*tkr_num              # rsi 30 송신 flag
f_rsi_70 = [0]*tkr_num              # rsi 70 송신 flag
trade_intv = 1                      # trade_intv 분 주기로 매매 감시
intv = 4                            # intv 시간 candle 참조
intv_s = "minute240"
fStart = timeBackup = num_buy = num_sell = minBack = hrBack = 0
# 시총 상위 종목 Ticker
tkr_buy = ["KRW-BTC", "KRW-ETH", "KRW-ADA", "KRW-XRP", "KRW-DOGE", "KRW-DOT", "KRW-BCH", "KRW-LTC", "KRW-LINK", "KRW-ETC"]     
     

# Keys
access = "UfxFeckqIxoheTgBcgN3KNa6vtP98WEWlyjDmHx6" 
secret = "NknKBgNg1cLnh8I4KYH2byIzvbDmx7171lrbxfLL"
myToken = "" 
myChannel = "#c-pjt"
upbit = Upbit(access, secret)
token = "1814838763:AAGNuB_LWtq8zJMHuezB-vsSI8C4b9X9QLk"
chat_id = 1883488213
#bot = telegram.Bot(token)

# Functions
#def send(str):
#    bot.sendMessage(chat_id,str)
	
def post_message(token, channel, text):
    # 슬랙 메시지 전송
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )
    time.sleep(0.1)
    return response

def get_start_time(ticker):
    # 시작 시간 조회
    df = get_ohlcvp(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_current_price(ticker):
    # 현재가 조회
    return get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def get_ohlc(ticker, intv):
    # 캔들 조회
    df = get_ohlcvp(ticker, interval=intv, count=1)
    ret = [df.iloc[0]['open'], df.iloc[0]['high'], df.iloc[0]['low'], df.iloc[0]['close']]
    return ret

def get_ma(ticker, intv, c, p):
    # 이동 평균선 조회
    df = get_ohlcvp(ticker, interval=intv, count=(c+p))
    ma = df['close'].rolling(c).mean().iloc[-p]
    return ma
    
def get_high(ticker, intv, c):
    # 고가 조회
    df = get_ohlcvp(ticker, interval=intv, count=c)
    high = df['high'].rolling(c).max().iloc[-1]
    return high

def get_low(ticker, intv, c):
    # 저가 조회
    df = get_ohlcvp(ticker, interval=intv, count=c)
    low = df['low'].rolling(c).min().iloc[-1]
    return low

def get_close_price(ticker, intv):
    # 전 시간 종가 return
    df = get_ohlcvp(ticker, interval=intv, count=2)
    close = df.iloc[0]['close']
    return close

def get_open_price(ticker, intv):
    # 전 시간 종가 return
    df = get_ohlcvp(ticker, interval=intv, count=1)
    open = df.iloc[0]['open']
    return open

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

def buy(tkr, balance):
    buy_result = upbit.buy_market_order(tkr, balance*0.999)
    if buy_result != None:
        return True
    else:
        return False

def sell(tkr):
    sell_result = upbit.sell_market_order(tkr, get_balance(tkr,"COIN"))
    if sell_result != None:
        return True
    else:
        return False

def buy_limit(tkr, price, balance):
    vol = balance / price
    buy_result = upbit.buy_limit_order(tkr, price, vol * 0.999)
    if buy_result != None:
        return True
    else:
        return False

def sell_limit(tkr, price):
    sell_result = upbit.sell_limit_order(tkr, price, get_balance(tkr,"COIN"))
    if sell_result != None:
        return True
    else:
        return False

def tick(price):
    if price < 10:
        return 0.01
    elif price < 100:
        return 0.1
    elif price < 1000:
        return 1
    elif price < 10000:
        return 5
    elif price < 100000:
        return 10
    elif price < 500000:
        return 50
    elif price < 1000000:
        return 100
    elif price < 2000000:
        return 500
    else:
        return 1000

def isNewCandle(intv, now):
    hour = now.hour
    if hour < 9:
        hour += 24
    hour -= 9
    if hour % intv == 0:
        return True
    else:
        return False

def select_tkrs(intv, c):
	# 데이터 스크래핑
    tkrs = get_tickers(fiat="KRW")
    vol =[0]*len(tkrs)
    data = [("tkr",0)] * len(tkrs)
    for i in range(0,len(tkrs)):
        df = get_ohlcvp(tkrs[i], intv, c)
        vol[i] = df.iloc[0]['price']
        data[i] = (tkrs[i], vol[i])
        time.sleep(0.1)
    data = sorted(data, key = lambda data: data[1], reverse = True)
	# 매수종목 선정
    top = ["KRW-"] * tkr_num
    for i in range(0, tkr_num):
        top[i] = data[i][0]
    
    return top

def sell_not_in():
# 탈락 종목 전량 매도
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

def buy_n_hold_start(curBalance):
    balance = (curBalance / tkr_num)
    ret = [0]*tkr_num
    for i in range(0,tkr_num):
        price = get_current_price(tkr_buy[i])
        ret[i] = balance / price
    return ret

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

def send_rsi(i):
    global f_rsi_30, f_rsi_70
    if rsi14[i] < 30 and f_rsi_30[i] != 1:
        if f_rsi_30[i] != 0:
            post_message(myToken, myChannel, tkr_buy[i]+" : rsi14 30 미만 감지("+str(round(rsi14[i],1))+")")
        f_rsi_30[i] = 1
    if rsi14[i] > 30 and f_rsi_30[i] != 2:
        if f_rsi_30[i] != 0:
            post_message(myToken, myChannel, tkr_buy[i]+" : rsi14 30 초과 감지("+str(round(rsi14[i],1))+")")
        f_rsi_30[i] = 2
    if rsi14[i] < 70 and f_rsi_70[i] != 1:
        if f_rsi_70[i] != 0:
            post_message(myToken, myChannel, tkr_buy[i]+" : rsi14 70 미만 감지("+str(round(rsi14[i],1))+")")
        f_rsi_70[i] = 1
    if rsi14[i] > 70 and f_rsi_70[i] != 2:
        if f_rsi_70[i] != 0:
            post_message(myToken, myChannel, tkr_buy[i]+" : rsi14 70 초과 감지("+str(round(rsi14[i],1))+")")
        f_rsi_70[i] = 2
		
		
		
		
		
		
