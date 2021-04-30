import time
import datetime
import requests
import pyupbit
from bs4 import BeautifulSoup

# Global variables
tkr_top20 = ["KRW-"]*20         # 거래량 상위 20종목 Ticker
tkr_buy = ["KRW-"]*20           # 매수할 종목 Ticker
tkr_num = 0                     # 선정된 종목 수
y_low_price = [0]*20            # 전일 저가 저장
tkr_ma5 = [0]*20                # 5일 이동평균선
fBuy = [0]*20                   # 금일 매수 여부
fSell = [0]*20                  # 금일 매도 여부
totalBalance = 0                # 현재 보유 원화
balance = 0                     # 각 종목별 매수 금액 = totalBalance / tkr_num

# Keys
access = "UfxFeckqIxoheTgBcgN3KNa6vtP98WEWlyjDmHx6" 
secret = "NknKBgNg1cLnh8I4KYH2byIzvbDmx7171lrbxfLL"
myToken = " " 
myChannel = "#c-pjt"

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
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ma5(ticker):
    # 5일 이동 평균선 조회
    df = pyupbit.get_ohlcv(ticker, interval="day", count=5)
    ma5 = df['close'].rolling(5).mean().iloc[-1]
    return ma5

def get_balance(coin):
    # 잔고 조회
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == coin:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0

def get_current_price(ticker):
    # 현재가 조회
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def select_tkrs(c):       # c==1 : 당일 Data, c==2 : 전일 Data
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
	# 매수종목 선정
    selected = 0
    for i in range(0,20):
        tmp = ticker_in_krw[i][:-4]
        tkr_top20[i] = "KRW-" + tmp
        if get_ma5(tkr_top20[i]) < get_current_price(tkr_top20[i]):         # 현재가가 5일 이평선보다 높은 경우 매수종목에 추가
            df = pyupbit.get_ohlcv(tkr_top20[i], interval="day", count=c)
            y_low_price[i] = df.iloc[0]['low']
            tkr_buy[selected] = tkr_top20[i]
            fBuy[i] = 0
            fSell[i] = 0
            selected += 1
            time.sleep(0.1)
    return selected



# Main Logic

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
# 시작 메세지 슬랙 전송
fSendTop20 = 1
num_buy = 0
num_sell = 0
tkr_num = select_tkrs(2)
remain = tkr_num
totalBalance = get_balance("KRW")
balance = totalBalance / tkr_num
now = datetime.datetime.now()
nowBackup = now
post_message(myToken, myChannel, "==================================")
post_message(myToken, myChannel, "autotrade start : "+str(now))
post_message(myToken, myChannel, "Total Balance : "+str(totalBalance))
post_message(myToken, myChannel, "Each Balance : "+str(balance))
post_message(myToken, myChannel, "=== Selected Tickers ===")
for i in range(0, tkr_num):
    post_message(myToken, myChannel, str(i+1)+" : "+tkr_buy[i])
    time.sleep(0.1)

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)

        if(now - datetime.timedelta(minutes=60) > nowBackup):
            nowBackup = now
            post_message(myToken, myChannel, "=== Running ===")

        totalBalanceBackup = totalBalance
        totalBalance = get_balance("KRW")
        if remain > 0:
            balance = totalBalance / remain
        else:
            balance = 0

        if totalBalance != totalBalanceBackup:
            post_message(myToken, myChannel, "=== Balance Changed ===")
            post_message(myToken, myChannel, "Total Balance : "+str(totalBalance))
            post_message(myToken, myChannel, "Each Balance : "+str(balance))

        time.sleep(1)


        # 09:00 ~ 08:55     매수 진행
        if start_time < now < end_time - datetime.timedelta(minutes=5):
            if fSendTop20 == 1:
                post_message(myToken, myChannel, "매수 감시")
                fSendTop20 = 0

            for i in range(0, tkr_num):
                # 매수 감시 : 현재가가 5일 이평선 이상 & 전일 저점 이상이면 매수
                if fBuy[i] == 0:
                    current_price = get_current_price(tkr_buy[i])
                    if get_ma5(tkr_buy[i]) <= current_price and y_low_price[i] <= current_price:
                        if balance > 5000:
                            buy_result = upbit.buy_market_order(tkr_buy[i], balance*0.999)
                            if buy_result != None:
                                fBuy[i] = 1
                                remain -= 1
                                post_message(myToken, myChannel, tkr_buy[i] + " buy : " +str(buy_result))            
                    time.sleep(0.5)
                # 매도 감시 : 현재가가 전일 저점 미만이면 매도
                else:
                    if fBuy[i] == 1:
                        current_price = get_current_price(tkr_buy[i])
                        if y_low_price[i] > current_price:
                            coin = get_balance(tkr_buy[i][4:])
                            if coin != None:
                                curBalance = get_current_price(tkr_buy[i]) * coin
                                if curBalance > 5000:
                                    sell_result = upbit.sell_market_order(tkr_buy[i], coin)
                                    if sell_result != None:
                                        fSell[i] = 1
                                        post_message(myToken, myChannel, tkr_buy[i] + " sell : " +str(sell_result))
                    time.sleep(0.5)
                time.sleep(0.5)

            
        # 08:55 ~ 09:00     전량 매도 후 종목 선정
        else:
            for i in range(0, tkr_num):
                coin = get_balance(tkr_buy[i][4:])
                if coin != None:
                    curBalance = get_current_price(tkr_buy[i]) * coin
                    if curBalance > 5000:
                        sell_result = upbit.sell_market_order(tkr_buy[i], coin)
                        if sell_result != None:
                            fBuy[i] = 0
                            fSell[i] = 0
                            post_message(myToken, myChannel, tkr_buy[i] + " sell : " +str(sell_result))
                time.sleep(0.5)
            time.sleep(0.5)

            if fSendTop20 == 0:
                post_message(myToken, myChannel, "전량 매도 & 종목 선정")
                tkr_num = select_tkrs(1)
                remain = tkr_num
                totalBalance = get_balance("KRW")
                balance = totalBalance / remain
                time.sleep(0.5)
                post_message(myToken, myChannel, "=== Balance Changed ===")
                post_message(myToken, myChannel, "Total Balance : "+str(totalBalance))
                post_message(myToken, myChannel, "Each Balance : "+str(balance))
                post_message(myToken, myChannel, "=== Selected Tickers ===")
                for i in range(0, 20):
                    post_message(myToken, myChannel, str(i+1)+" : "+tkr_buy[i])
                    time.sleep(0.1)
                fSendTop20 = 1

        time.sleep(1)

    except Exception as e:
        print(e)
        post_message(myToken, myChannel, e)
        time.sleep(1)
