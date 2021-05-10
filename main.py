from vars_funcs import *
# Main Logic

# 로그인
fStart = timeBackup = num_buy = num_sell = 0
# 시작 메세지 슬랙 전송
post_message(myToken, myChannel, "==================================")
post_message(myToken, myChannel, "autotrade start (ver."+VERSION+"))")
post_message(myToken, myChannel, "==================================")

while True:
    try:
        now = datetime.datetime.now()
    # 매일 09시 마다 신규 종목 선정
        if timeBackup != now.hour or fStart == 0:
            if now.hour == 9 or fStart == 0:
                last_trade_time = [now - datetime.timedelta(minutes=30)]*5
            # 신규 종목 선정 및 목표가 계산
                post_message(myToken, myChannel, "=== 종목 선정 시작 : "+str(datetime.datetime.now()))
                tmp = select_tkrs()
                tkr_buy = ['KRW-BTC', 'KRW-ETH', ' ', ' ', ' ']
                j = 2
                for i in range(0, 5):
                    if tmp[i] != 'KRW-BTC' and tmp[i] != 'KRW-ETH':
                        tkr_buy[j] = tmp[i]
                        j += 1
                        if j >= 5:
                            break

                post_message(myToken, myChannel, "=== 종목 선정 완료 : "+str(datetime.datetime.now()))
                post_message(myToken, myChannel, str(tkr_buy))
            # 탈락 종목 전량 매도
                post_message(myToken, myChannel, "=== 미포함 종목 매도 : "+str(datetime.datetime.now()))
                balances = upbit.get_balances()
                time.sleep(0.1)
                for b in balances:
                    if b['currency'] != 'KRW' and b['currency'] != 'VTHO':
                        tkr = "KRW-"+b['currency']
                        if tkr not in tkr_buy:
                            if get_balance(tkr,"KRW") > 5000:
                                sell(tkr)
                                num_sell += 1
                            time.sleep(0.1)
            # 잔고 Update
                startBalance = get_totalKRW()

        # 1시간 마다 매매 결과 송신
            curBalance = get_totalKRW()
            balChange_hr = curBalance - hourlyBalance
            balChngPercent_hr = balChange_hr / hourlyBalance * 100
            balChange_d = curBalance - startBalance
            balChngPercent_d = balChange_d / startBalance * 100
            hourlyBalance = curBalance
            balance[0] = balance[1] = curBalance * 0.35
            balance[0] = balance[1] = balance[3] = curBalance * 0.1
            post_message(myToken, myChannel, "=== Hourly Report ===")
            post_message(myToken, myChannel, " - 매수 : "+str(num_buy)+"회, 매도 : "+str(num_sell)+"회")
            post_message(myToken, myChannel, " - 시작 잔고 : "+str(round(balanceBackup))+"원")
            post_message(myToken, myChannel, " - 종료 잔고 : "+str(round(totalBalance))+"원")
            post_message(myToken, myChannel, " - 수익 : "+str(round(balChange))+"원 ("+str(round(balChngPercent, 2))+"%)")
            post_message(myToken, myChannel, "=== "+str(now.hour)+"시 매매 시작 ===")
            num_buy = num_sell = 0
            timeBackup = now.hour


    # 매매 logic
        now = datetime.datetime.now()
        for i in range(0, 5):
            if now - datetime.timedelta(minutes=30) > last_trade_time[i]:
                tkr = tkr_buy[i]
                balanceDiff = balance[i] - get_balance(tkr_buy[i],"KRW")
                # 매수
                if balanceDiff > 5000:
                    current = get_current_price(tkr)
                    ma7 = get_ma(tkr, "day", 7, 1)
                    # 기준선보다 높으면 매수
                    if current > ma7:
                        buy(tkr, balanceDiff)
                        last_trade_time[i] = now
                        num_buy += 1
                # 매도
                elif get_balance(tkr_buy[i],"KRW") > 5000:
                    current = get_current_price(tkr)
                    ma7 = get_ma(tkr, "day", 7, 1)
                    # 기준선보다 낮으면 매도
                    if current < ma7:
                        sell(tkr)
                        last_trade_time[i] = now
                        num_sell += 1
                time.sleep(0.1)
        time.sleep(1)      
        

    except Exception as e:
        print(e)
        post_message(myToken, myChannel, e)
        time.sleep(1)
