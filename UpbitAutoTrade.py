import time
import datetime
import requests
import pyupbit
from bs4 import BeautifulSoup

# Global variables
VERSION = "2021.05.02.00"
tkr_top20 = ["KRW-"]*20         # 거래량 상위 20종목 Ticker
tkr_buy = ["KRW-"]*20           # 매수할 종목 Ticker
tkr_num = 0                     # 선정된 종목 수
y_low_price = [0]*20            # 전일 저가 저장
sell_price = [0]*20             # 매도가 저장
buy_price = [0]*20              # 매수가 저장
tkr_ma5 = [0]*20                # 5일 이동평균선
min_avg_15_60 = [0, 0]          # 15분, 60분 평균
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

def get_min_avg(ticker):
    # 15분, 60분 이동 평균선 조회
    min_avg = [0, 0]
    df = pyupbit.get_ohlcv(ticker, interval="minute", count=60)
    min_avg[0] = df['close'].rolling(15).mean().iloc[-1]
    min_avg[1] = df['close'].rolling(60).mean().iloc[-1]
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
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def buy(tkr, cur_price):
    buy_result = upbit.buy_market_order(tkr, balance*0.999)
    if buy_result != None:
        buy_price[i] = cur_price
        post_message(myToken, myChannel, tkr + " buy : " +str(buy_result))  
        return True
    else:
        return False

def sell(tkr, cur_price):
    sell_result = upbit.sell_market_order(tkr, get_balance(tkr,"COIN"))
    if sell_result != None:
        sell_price[i] = cur_price
        post_message(myToken, myChannel, tkr + " sell : " +str(sell_result))
        return True
    else:
        return False

def select_tkrs(c):       # c==1 : 당일 Data, c==2 : 전일 Data
	# 데이터 스크래핑
    tkrs = pyupbit.get_tickers(fiat="KRW")
    vol =[0]*len(tkrs)
    data = [("tkr",0)] * len(tkrs)
    for i in range(0,len(tkrs)):
        df = pyupbit.get_ohlcv(tkrs[i], 'day', c)
        vol[i] = df.iloc[0]['volume'] * df.iloc[0]['close']
        data[i] = (tkrs[i], vol[i])
        time.sleep(0.1)
    data = sorted(data, key = lambda data: data[1], reverse = True)
	# 매수종목 선정
    selected = 0
    for i in range(0,20):
        tkr_top20[i] = data[i][0]
        if get_ma5(tkr_top20[i]) < get_current_price(tkr_top20[i]):         # 현재가가 5일 이평선보다 높은 경우 매수종목에 추가
            df = pyupbit.get_ohlcv(tkr_top20[i], interval="day", count=c)
            y_low_price[i] = df.iloc[0]['low']
            tkr_buy[selected] = tkr_top20[i]
            if(get_balance(tkr_buy[i],"KRW") > 5000):
                fBuy[i] = 1
                num_buy += 1
            else:
                fBuy[i] = 0
            fSell[i] = 0
            selected += 1
            time.sleep(0.1)
    
    return selected

select_tkrs(1)
# Main Logic

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
# 시작 메세지 슬랙 전송
fSendTop20 = 1
fStart = 0
num_buy = num_sell = remain = 0
now = datetime.datetime.now()
tBack = now.hour
post_message(myToken, myChannel, "==================================")
post_message(myToken, myChannel, "autotrade start (ver."+VERSION+"))")

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)

        if fStart == 1:
            if now.hour != tBack:
                tBack = now.hour
                post_message(myToken, myChannel, "=== Running ===")
                post_message(myToken, myChannel, "매수 : "+str(num_buy-num_sell)+" / 매도 : "+str(num_sell)+" / 대기 : "+str(remain))
                post_message(myToken, myChannel, "Total Balance : "+str(totalBalance))
                post_message(myToken, myChannel, "Each Balance : "+str(balance))

            totalBalanceBackup = totalBalance
            totalBalance = get_krw()
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
                post_message(myToken, myChannel, "종목 선정 : "+str(datetime.datetime.now()))
                remain = tkr_num = select_tkrs(2)
                remain -= num_buy
                totalBalance = get_krw()
                balance = totalBalance / remain
                num_buy = num_sell = 0
                time.sleep(0.5)
                
                post_message(myToken, myChannel, "=== Selected Tickers ===")
                for i in range(0, tkr_num):
                    buy_price[i] = sell_price[i] = 0
                    post_message(myToken, myChannel, str(i+1)+" : "+tkr_buy[i])
                    time.sleep(0.1)

                post_message(myToken, myChannel, "매매 시작 : "+str(datetime.datetime.now()))
                fSendTop20 = 0
                fStart = 1

            for i in range(0, tkr_num):
                # 매수 감시 : 현재가가 5일 이평선 이상 & 전일 저점 이상이면 매수
                if get_balance(tkr_buy[i],"KRW") < 5000 and balance > 5000 and buy_price[i] == 0:
                    current_price = get_current_price(tkr_buy[i])
                    if get_ma5(tkr_buy[i]) <= current_price and y_low_price[i] <= current_price:
                        if buy(tkr_buy[i], current_price):
                            num_buy += 1
                            remain -= 1
                            print("매수 : 현재가 5일 이평선 이상 and 전일 저점 이상")
                    time.sleep(0.1)
                # 매도 감시 : 현재가가 전일 저점 미만이면 매도
                else:
                    # 매도 조건 판단
                    if get_balance(tkr_buy[i],"KRW") > 5000:   #fBuy[i] == 1 and fSell[i] == 0:
                        current_price = get_current_price(tkr_buy[i])
                        df = pyupbit.get_ohlcv(tkr_buy[i], interval="day", count=1)
                        high_price = df.iloc[0]['high']
                        open_price = df.iloc[0]['open']
                        raise_rate = high_price / open_price
                        fallen_rate = current_price / open_price
                        min_avg_15_60 = get_min_avg(tkr_buy[i])
                        # 1. 전일 저점보다 낮거나 5%이상 하락한 경우 매도
                        # 2. 30% 이상 상승 후 15분 평균가가 60분 평균가보다 낮아지는 경우 매도
                        if (y_low_price[i] > current_price or fallen_rate < 0.95) or (raise_rate > 1.3 and min_avg_15_60[0] < min_avg_15_60[1]):
                            if sell(tkr_buy[i], current_price):
                                num_sell += 1
                                if (y_low_price[i] > current_price or fallen_rate < 0.95):
                                    print("매도 : 전일 저점 이하 or 5%이상 하락")
                                else:
                                    print("30% 이상 상승 후 15분 평균가가 60분 평균가 미만")
                    # 매도 후 재 매수 조건 판단
                    elif sell_price[i] != 0:
                        current_price = get_current_price(tkr_buy[i])
                        df = pyupbit.get_ohlcv(tkr_buy[i], interval="day", count=1)
                        high_price = df.iloc[0]['high']
                        low_price = df.iloc[0]['low']
                        target_price = sell_price[i] + ((high_price + low_price) * 0.5)
                        # 현재가가 매도가 + (고가 - 저가) * K 보다 높아진 경우
                        if target_price <= current_price and balance > 5000:
                            if buy(tkr_buy[i], current_price):
                                num_sell -= 1
                                print("재매수 : 현재가가 (매도가+(고가-저가)*K) 이상 상승")
                        time.sleep(0.1)
                    time.sleep(0.1)
                time.sleep(0.5)

            
        # 08:55 ~ 09:00     전량 매도
        else:
            if fSendTop20 == 0:
                post_message(myToken, myChannel, "매매 종료 : "+str(datetime.datetime.now()))
                fSendTop20 = 1
            for i in range(0, tkr_num):
                if get_balance(tkr_buy[i],"KRW") > 5000:
                    sell(tkr_buy[i], 0)
                time.sleep(0.1)

        time.sleep(1)

    except Exception as e:
        print(e)
        post_message(myToken, myChannel, e)
        time.sleep(1)
