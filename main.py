from vars_funcs import *
# Main Logic

# 로그인
fStart = timeBackup = num_buy = num_sell = minBack = hrBack = 0
# 시작 메세지 슬랙 전송
post_message(myToken, myChannel, "==================================")
post_message(myToken, myChannel, "autotrade start (ver."+VERSION+"))")
post_message(myToken, myChannel, "==================================")

while True:
    try:
        now = datetime.datetime.now()
    # 매일 08시 57분 신규 종목 선정
        if timeBackup != now.hour or fStart == 0 or (now.hour == 8 and now.minute == 59):
            if (fStart == 0) or (now.hour == 8 and now.minute == 59):
                last_trade_time = [now - datetime.timedelta(minutes=10)]*10
            # 신규 종목 선정 및 목표가 계산
                post_message(myToken, myChannel, "=== 종목 선정 시작 : "+str(datetime.datetime.now()))
                if now.hour >= 9:
                    tmp = select_tkrs('day', 2)
                else:
                    tmp = select_tkrs('day', 1)

                tkr_buy[0] = 'KRW-BTC'
                tkr_buy[1] = 'KRW-ETH'
                j = 2
                for i in range(0, 15):
                    if tmp[i] != 'KRW-BTC' and tmp[i] != 'KRW-ETH':
                        tkr_buy[j] = tmp[i]
                        j += 1
                        if j >= 10:
                            break

                post_message(myToken, myChannel, "=== 종목 선정 완료 : "+str(datetime.datetime.now()))
                post_message(myToken, myChannel, str(tkr_buy))
            # 탈락 종목 전량 매도
                post_message(myToken, myChannel, "=== 미포함 종목 매도 : "+str(datetime.datetime.now()))
                balances = upbit.get_balances()
                time.sleep(0.1)
                for b in balances:
                    if b['currency'] != 'KRW' and float(b['avg_buy_price']) > 0:
                        tkr = "KRW-"+b['currency']
                        if tkr not in tkr_buy:
                            if get_balance(tkr,"KRW") > 5000:
                                sell(tkr)
                                num_sell += 1
                            time.sleep(0.1)
                if fStart == 0:
                    for i in range(0,10):
                        close_price[i] = get_open_price(tkr_buy[i], "day")
            # 잔고 Update
                startBalance = get_totalKRW()
                hourlyBalance = startBalance
                fStart = 1
        # 1시간 마다 매매 결과 송신
            curBalance = get_totalKRW()
            balChange_hr = curBalance - hourlyBalance
            balChngPercent_hr = balChange_hr / hourlyBalance * 100
            balChange_d = curBalance - startBalance
            balChngPercent_d = balChange_d / startBalance * 100
            hourlyBalance = curBalance
            balance[0] = balance[1] = curBalance * 0.15
            for i in range(2, 10):
                balance[i] = curBalance * 0.08
            post_message(myToken, myChannel, "=== Hourly Report ===")
            post_message(myToken, myChannel, " - 매수 : "+str(num_buy)+"회, 매도 : "+str(num_sell)+"회")
            post_message(myToken, myChannel, " - 잔고 : "+str(round(curBalance))+"원")
            post_message(myToken, myChannel, " - 시간 수익 : "+str(round(balChange_hr))+"원 ("+str(round(balChngPercent_hr, 2))+"%)")
            post_message(myToken, myChannel, " - 금일 수익 : "+str(round(balChange_d))+"원 ("+str(round(balChngPercent_d, 2))+"%)")
            num_buy = num_sell = 0
            timeBackup = now.hour


    # 매매 logic
        while minBack == now.minute:
            now = datetime.datetime.now()
        minBack = now.minute
        for i in range(0, 10):
            tkr = tkr_buy[i]
            balanceDiff = balance[i] - get_balance(tkr,"KRW")
        # 이전 캔들 종가 Update
            #if now.minute % 30 <= 1:
            #close_price[i] = get_open_price(tkr, "day")
            #fBuy[i] = 0
        # 매수
            if balanceDiff > 5000 and close_price[i] > 0:
                current = get_current_price(tkr)
                if current > (close_price[i] + tick(current)):
                    buy(tkr, balanceDiff)
                    last_trade_time[i] = now
                    #fBuy[i] = 1
                    num_buy += 1
        # 매도
            elif get_balance(tkr_buy[i],"KRW") > 5000:
                current = get_current_price(tkr)
                if current < (close_price[i] - tick(current)):
                    sell(tkr)
                    last_trade_time[i] = now
                    num_sell += 1
            time.sleep(0.1)

        

    except Exception as e:
        print(e)
        post_message(myToken, myChannel, e)
        time.sleep(1)
