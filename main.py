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

    # 종목 선정
        if fSelect == 0:
            while not start_time < now < end_time:
                None
            post_message(myToken, myChannel, "종목 선정 시작 : "+str(datetime.datetime.now()))
            if fStart == 0:
                tkr_top20 = select_tkrs(2)
                for i in range(0,20):
                    target_price[i] = get_ohlcvp(tkr_top20[i], 'day', 2).iloc[0]['close']
                    if get_balance(tkr_top20[i],"KRW") > 5000:
                        remain -= 1
                    time.sleep(0.1)
                fStart = 1
            else:
                tkr_top20_new = select_tkrs(2)
                for i in range(0,20):
                    target_price[i] = get_ohlcvp(tkr_top20[i], 'day', 2).iloc[0]['close']
                    if get_balance(tkr_top20[i],"KRW") > 5000:
                        if tkr_top20[i] not in tkr_top20_new:
                            sell(tkr_top20[i])
                        else:
                            remain -= 1
                    time.sleep(0.1)
                tkr_top20 = tkr_top20_new
            post_message(myToken, myChannel, "종목 선정 완료 : "+str(datetime.datetime.now()))
            post_message(myToken, myChannel, str(tkr_top20))
            fSelect = 1

    # 잔고 Update
        totalBalanceBackup = totalBalance
        totalBalance = get_krw()
        if remain > 0:
            balance = totalBalance / remain
        else:
            balance = 0

    # 1시간마다 메시지 송신
        if(timeBackup != now.hour):
            post_message(myToken, myChannel, "still running")
            post_message(myToken, myChannel, "매수 : "+str(num_buy)+" / 매도 : "+str(num_sell))
            timeBackup = now.hour
            if now.hour == 9:
                num_buy = num_sell = 0
                fSelect = 0

    # 매매 logic
        for i in range(0, 20):
            tkr = tkr_top20[i]
            current = get_current_price(tkr)
            ma_s = get_min_avg(tkr, 5, 1)
            ma_s_old = get_min_avg(tkr, 5, 3)
            diff_s = (ma_s - ma_s_old) / ma_s_old * 100 
            ma_l = get_min_avg(tkr, 15, 1)
            ma_l_old = get_min_avg(tkr, 15, 3)
            diff_l = (ma_l - ma_l_old) / ma_l_old * 100 
            # 매수
            if (get_balance(tkr_top20[i],"KRW") < 5000) and balance > 5000:
                # 5분 이평선 3분 전 대비 0.1% 상승 && 현재가 15분 이평선 초과
                if diff_s > 0.1 and current > ma_l:
                    if buy(tkr, balance) == True:
                        num_buy += 1
                        remain -= 1
            # 매도
            elif get_balance(tkr_top20[i],"KRW") > 5000:
                # 5분 이평선 3분 전 대비 하락 && 현재가 15분 이평선 미만
                if diff_s < 0 and current < ma_l:
                    if sell(tkr) == True:
                        num_sell += 1
                        remain += 1
            time.sleep(0.2)
        time.sleep(1)

    except Exception as e:
        print(e)
        post_message(myToken, myChannel, e)
        time.sleep(1)
