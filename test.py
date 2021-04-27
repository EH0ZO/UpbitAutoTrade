import time
import datetime
import requests
import pyupbit
from bs4 import BeautifulSoup

# Global variables
K = 0.5
krw = "KRW-"
ticker_top20 = ["KRW-"]*20
target_price = [0]*20
close_price = [0]*20
fBough = [0]*20
totalBalance = 0
balance = 0

# Keys
access = "UfxFeckqIxoheTgBcgN3KNa6vtP98WEWlyjDmHx6" 
secret = "NknKBgNg1cLnh8I4KYH2byIzvbDmx7171lrbxfLL"
myToken = "xoxb-2017388466625-2030096085360-KKa1FMEc5JTa3sfGQxkYNZk7" 
myChannel = "#c-pjt"

# Functions
def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

def get_balance(coin):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == coin:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def get_top20():
	# 데이터 스크래핑
    url = "https://www.coingecko.com/ko/거래소/upbit"
    resp = requests.get(url)
	# 데이터 선택
    bs = BeautifulSoup(resp.text,'html.parser')
    selector = "tbody > tr > td > a"
    columns = bs.select(selector)
	# Ticker 추출
    ticker_in_krw = [x.text.strip() for x in columns if x.text.strip()[-3:] == "KRW"]
    time.sleep(1)
	# Top20 및 목표가 추출
    for i in range(0,20):
        tmp = ticker_in_krw[i][:-4]
        ticker_top20[i] = krw + tmp
        df = pyupbit.get_ohlcv(ticker_top20[i], interval="day", count=1)
        target_price[i] = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * K
        close_price[i] = df.iloc[0]['close']
        fBough[i] = 0
        time.sleep(0.1)



# Main Logic

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
# 시작 메세지 슬랙 전송
fRun = 1
fSendTop20 = 0
remain = 20
get_top20()
totalBalance = get_balance("KRW")
balance = totalBalance / remain
now = datetime.datetime.now()
post_message(myToken, myChannel, "==================================")
post_message(myToken, myChannel, "autotrade start : "+str(now))
post_message(myToken, myChannel, "Total Balance : "+str(totalBalance))
post_message(myToken, myChannel, "Each Balance : "+str(balance))
post_message(myToken, myChannel, "=== TOP20 Tickers ===")
for i in range(0, 20):
    post_message(myToken, myChannel, str(i+1)+" : "+ticker_top20[i]+"  C:"+str(round(close_price[i],2))+"/T:"+str(round(target_price[i], 2)))
    time.sleep(0.1)

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)

        totalBalanceBackup = totalBalance
        totalBalance = get_balance("KRW")
        balance = totalBalance / remain
        if totalBalance != totalBalanceBackup:
            post_message(myToken, myChannel, "=== Balance Changed ===")
            post_message(myToken, myChannel, "Total Balance : "+str(totalBalance))
            post_message(myToken, myChannel, "Each Balance : "+str(balance))

        time.sleep(1)


        # 09:00 ~ 08:50     목표가 도달 시 매수
        if start_time < now < end_time - datetime.timedelta(minutes=10):
            #if fRun == 1:
            if fSendTop20 == 1:
                post_message(myToken, myChannel, "매수 감시")
                fSendTop20 = 0

            for i in range(0, 20):
                if fBough[i] == 0:
                    current_price = get_current_price(ticker_top20[i])
                    if target_price[i] < current_price:
                        if balance > 5000:
                            buy_result = upbit.buy_market_order(ticker_top20[i], balance*0.999)
                            if buy_result != None:
                                fBough[i] = 1
                                remain -= 1
                                post_message(myToken, myChannel, ticker_top20[i] + " buy : " +str(buy_result))
                        time.sleep(1)
                else:
                    current_price = get_current_price(ticker_top20[i])
                    if close_price[i] > current_price:
                        coin = get_balance(ticker_top20[i][4:])
                        if coin != None:
                            curBalance = get_current_price(ticker_top20[i]) * coin
                            if curBalance > 5000:
                                sell_result = upbit.sell_market_order(ticker_top20[i], coin*0.999)
                                if sell_result != None:
                                    fBough[i] = 0
                                    post_message(myToken, myChannel, ticker_top20[i] + " sell : " +str(sell_result))
                        time.sleep(1)
            time.sleep(1)

            
        # 08:50 ~ 09:00     전량 매도 후 종목 선정
        else:
            #fRun = 1
            for i in range(0, 20):
                coin = get_balance(ticker_top20[i][4:])
                if coin != None:
                    curBalance = get_current_price(ticker_top20[i]) * coin
                    if curBalance > 5000:
                        sell_result = upbit.sell_market_order(ticker_top20[i], coin*0.999)
                        if sell_result != None:
                            fBough[i] = 0
                            post_message(myToken, myChannel, ticker_top20[i] + " sell : " +str(sell_result))
                time.sleep(0.1)
            time.sleep(1)

            remain = 20
            totalBalance = get_balance("KRW")
            balance = totalBalance / remain

            if fSendTop20 == 0:
                post_message(myToken, myChannel, "전량 매도 & 종목 선정")
                get_top20()
                time.sleep(1)
                post_message(myToken, myChannel, "totalBalance : "+str(totalBalance))
                post_message(myToken, myChannel, "balance : "+str(balance))
                post_message(myToken, myChannel, "TOP20 Tickers")
                for i in range(0, 20):
                    post_message(myToken, myChannel, str(i+1)+" : "+ticker_top20[i])
                    time.sleep(0.1)
                fSendTop20 = 1

        time.sleep(1)

    except Exception as e:
        print(e)
        post_message(myToken, myChannel, e)
        time.sleep(1)
