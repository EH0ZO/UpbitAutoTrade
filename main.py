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
            timeBackup = now.hour

    # 종목 선정
        # 최초 시작 시 종목 선정
        if fStart == 0:
            tkr_top20 = select_tkrs(6)
            for i in range(0,20):
                if get_balance(tkr_top20[i],"KRW") > 5000:
                    remain -= 1
                    time.sleep(0.1)
            fSend = 0
            fStart = 1
        # 6시간마다 종목 갱신
        elif now.hour % 6 == 0:
            if fSelect == 0:
                tkr_top20_new = select_tkrs(6)
                for i in range(0,20):
                    if get_balance(tkr_top20[i],"KRW") > 5000 and tkr_top20[i] not in tkr_top20_new:
                        sell(tkr_top20[i])
                        time.sleep(0.2)
                tkr_top20 = tkr_top20_new
                fSend = 0
                fSelect = 1
        else:
            fSelect = 0
        
        if fSend == 0:
            #print(tkr_top20)
            post_message(myToken, myChannel, "종목 선정 완료 : "+str(datetime.datetime.now()))
            post_message(myToken, myChannel, str(tkr_top20))
            fSend = 1

    # 잔고 Update
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
            #print(str(totalBalance)+"/"+str(balance)+"/"+str(remain))
        
    # 매매 logic
        for i in range(0, 20):
            tkr = tkr_top20[i]
            K = 0
            now = datetime.datetime.now()
            # 최근 거래 5분 경과 후
            if now - datetime.timedelta(minutes=5) > last_trade_time[i]:
                # 매수 감시 : (60분 평균가 > 180분 평균가*(1+K)) && (현재가 > 60분 평균가*(1+K))
                if (get_balance(tkr_top20[i],"KRW") < 5000) and balance > 5000:
                    current = get_current_price(tkr)
                    min_avg_60 = get_min_avg(tkr, 60)
                    min_avg_180 = get_min_avg(tkr, 180)
                    #print(tkr+"/"+str(min_avg_60)+"/"+str(min_avg_180))
                    if (min_avg_60 > min_avg_180*(1+K)) and (current > min_avg_60*(1+K)):
                        buy(tkr, balance)
                        last_trade_time[i] = now
                        remain -= 1
                # 매도 감시 : (60분 평균가 < 180분 평균가*(1-K)) && (현재가 < 60분 평균가*(1-K))
                elif get_balance(tkr_top20[i],"KRW") > 5000:
                    current = get_current_price(tkr)
                    min_avg_60 = get_min_avg(tkr, 60)
                    min_avg_180 = get_min_avg(tkr, 180)
                    if (min_avg_60 < min_avg_180*(1-K)) or (current < min_avg_60*(1-K)):
                        sell(tkr)
                        last_trade_time[i] = now
                        remain += 1
                time.sleep(0.2)
        time.sleep(1)

    except Exception as e:
        print(e)
        post_message(myToken, myChannel, e)
        time.sleep(1)
