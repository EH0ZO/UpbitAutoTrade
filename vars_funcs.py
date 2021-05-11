from pyupbit2 import *
import time
import datetime
import requests
from bs4 import BeautifulSoup

# Global variables
VERSION = "21.05.12.18"
tkr_buy = ["KRW-"]*15               # 거래량 상위 10종목 Ticker
close_price = [0]*15                # 매매 기준가
startBalance = 0                    # 09시 기준 잔고
hourlyBalance = 0                   # 매시 정각 기준 잔고
totalBalance = 0                    # 현재 보유 원화
balanceBackup = 0                   # 이전 보유 원화
balance = [0]*15                    # 종목별 거래금액
num_buy = 0                         # 매수 횟수
num_sell = 0                        # 매도 횟수

# Keys
access = "UfxFeckqIxoheTgBcgN3KNa6vtP98WEWlyjDmHx6" 
secret = "NknKBgNg1cLnh8I4KYH2byIzvbDmx7171lrbxfLL"
myToken = "" 
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

def get_current_price(ticker):
    # 현재가 조회
    return get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

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

def get_close_price(ticker):
    # 전일 종가 return
    df = get_ohlcvp(ticker, interval="day", count=2)
    close = df.iloc[0]['close']
    return close

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

def select_tkrs():
	# 데이터 스크래핑
    tkrs = get_tickers(fiat="KRW")
    vol =[0]*len(tkrs)
    data = [("tkr",0)] * len(tkrs)
    for i in range(0,len(tkrs)):
        df = get_ohlcvp(tkrs[i], 'day', 2)
        vol[i] = df['price'].rolling(2).sum().iloc[-1]
        data[i] = (tkrs[i], vol[i])
        time.sleep(0.1)
    data = sorted(data, key = lambda data: data[1], reverse = True)
	# 매수종목 선정
    top15 = ["KRW-"]*15
    for i in range(0,15):
        top15[i] = data[i][0]
    
    return top15
