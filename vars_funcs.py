from pyupbit2 import *
import time
import datetime
import requests
from bs4 import BeautifulSoup

# Global variables
VERSION = "21.05.03.00"
tkr_top20 = ["KRW-"]*20         # 거래량 상위 20종목 Ticker (기존)
tkr_top20_new = ["KRW-"]*20     # 거래량 상위 20종목 Ticker (신규)
totalBalance = 0                # 현재 보유 원화
balance = 0                     # 각 종목별 매수 금액 = totalBalance / tkr_num

# Keys
access = "UfxFeckqIxoheTgBcgN3KNa6vtP98WEWlyjDmHx6" 
secret = "NknKBgNg1cLnh8I4KYH2byIzvbDmx7171lrbxfLL"
myToken = " " 
myChannel = "#c-pjt"
upbit = Upbit(access, secret)

# Functions
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

def get_ma5(ticker):
    # 5일 이동 평균선 조회
    df = get_ohlcvp(ticker, interval="day", count=5)
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    return ma5

def get_min_avg(ticker, minute):
    # minute분 평균가 조회
    df = get_ohlcvp(ticker, interval="minute", count=minute)
    min_avg = df['close'].rolling(minute).mean().iloc[-1]
    return min_avg

def get_krw():
    # 잔고 조회
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == "KRW":
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0

def get_balance(tkr, sel):
    # 잔고 조회
    coin = tkr[4:]
    balances = upbit.get_balances()
    ret = 0
    for b in balances:
        if b['currency'] == coin:
            if b['balance'] is not None:
                ret = float(b['balance'])
            else:
                ret = 0
    
    if sel == "COIN":
        return ret
    elif sel == "KRW":
        return ret * get_current_price("KRW-"+coin)
    else:
        return 0

def get_current_price(ticker):
    # 현재가 조회
    return get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def buy(tkr):
    buy_result = upbit.buy_market_order(tkr, global.balance*0.999)
    if buy_result != None:
        post_message(myToken, myChannel, tkr + " buy : "+tkr)  
        return True
    else:
        return False

def sell(tkr):
    sell_result = upbit.sell_market_order(tkr, get_balance(tkr,"COIN"))
    if sell_result != None:
        post_message(myToken, myChannel, tkr + " sell : "+tkr)
        return True
    else:
        return False

def select_tkrs():       # c==1 : 당일 Data, c==2 : 전일 Data
    now = datetime.datetime.now()
    if now.hour < 12:
        c = 2
    else:
        c = 1
	# 데이터 스크래핑
    tkrs = get_tickers(fiat="KRW")
    vol =[0]*len(tkrs)
    data = [("tkr",0)] * len(tkrs)
    for i in range(0,len(tkrs)):
        df = get_ohlcvp(tkrs[i], 'day', c)
        vol[i] = df.iloc[0]['price']
        data[i] = (tkrs[i], vol[i])
        time.sleep(0.1)
    data = sorted(data, key = lambda data: data[1], reverse = True)
    print(data)
	# 매수종목 선정
    top20 = [0]*20
    for i in range(0,20):
        top20[i] = data[i][0]
    
    return top20