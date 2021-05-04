from vars_funcs import *
# Main Logic

# 로그인
fStart = fSelect = fSend = timeBackup = 0
# 시작 메세지 슬랙 전송
post_message(myToken, myChannel, "==================================")
post_message(myToken, myChannel, "autotrade start (ver."+VERSION+"))")

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)

        if(timeBackup != now.hour):
            post_message(myToken, myChannel, "still running")
            post_message(myToken, myChannel, "매수 : "+str(num_buy)+" / 매도 : "+str(num_sell))
            timeBackup = now.hour
            if now.hour == 9:
                num_buy = num_sell = 0

    # 종목 선정
        # 최초 시작 시 종목 선정
        if fStart == 0:
            tkr_top20 = select_tkrs(6)
            for i in range(0,20):
                if get_balance(tkr_top20[i],"KRW") > 5000:
                    remain -= 1
                    time.sleep(0.1)
            fSend = fStart = fSelect = 1
        # 6시간마다 종목 갱신
        elif now.hour % 6 == 0:
            if fSelect == 0:
                tkr_top20_new = select_tkrs(6)
                for i in range(0,20):
                    if get_balance(tkr_top20[i],"KRW") > 5000 and tkr_top20[i] not in tkr_top20_new:
                        sell(tkr_top20[i])
                        time.sleep(0.2)
                tkr_top20 = tkr_top20_new
                fSend = fSelect = 1
        else:
            fSelect = 0
        
        if fSend == 1:
            post_message(myToken, myChannel, "종목 선정 완료 : "+str(datetime.datetime.now()))
            post_message(myToken, myChannel, str(tkr_top20))
            fSend = 0

    # 잔고 Update
        totalBalanceBackup = totalBalance
        totalBalance = get_krw()
        if remain > 0:
            balance = totalBalance / remain
        else:
            balance = 0
    # 매매 logic
        for i in range(0, 20):
            tkr = tkr_top20[i]
            now = datetime.datetime.now()
            # 최근 거래 5분 경과 후
            if now - datetime.timedelta(minutes=10) > last_trade_time[i]:
                # 매수
                if (get_balance(tkr_top20[i],"KRW") < 5000) and balance > 5000:
                    if buy(tkr, balance) == True:
                        num_buy += 1
                        last_trade_time[i] = now
                        remain -= 1
                # 매도
                elif get_balance(tkr_top20[i],"KRW") > 5000:
                    if sell(tkr) == True:
                        num_sell += 1
                        last_trade_time[i] = now
                        remain += 1
                time.sleep(0.2)
        time.sleep(1)

    except Exception as e:
        print(e)
        post_message(myToken, myChannel, e)
        time.sleep(1)
