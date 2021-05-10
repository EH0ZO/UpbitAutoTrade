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

    # 1시간 마다 신규 종목 선정
        if(timeBackup != now.hour):
        # 신규 종목 선정 및 목표가 계산
        	if now.hour == 9 or fStart == 0
            	post_message(myToken, myChannel, "=== 종목 선정 시작 : "+str(datetime.datetime.now()))
            	tkr_top10 = select_tkrs()
            for i in range(0,10):
                # 목표가 : 전 시간 종가 + (전 시간 고점 - 저점) * K
                ret = get_target_prce(tkr_top10[i])
                buy_price[i] = ret[0]
                sell_price[i] = ret[1]
                time.sleep(0.1)
            post_message(myToken, myChannel, "=== 종목 선정 완료 : "+str(datetime.datetime.now()))
            post_message(myToken, myChannel, str(tkr_top10))
        # 탈락 종목 전량 매도
            post_message(myToken, myChannel, "=== 탈락 종목 매도 : "+str(datetime.datetime.now()))
            balances = upbit.get_balances()
            time.sleep(0.1)
            for b in balances:
                if b['currency'] != 'KRW':
                    tkr = "KRW-"+b['currency']
                    if tkr not in tkr_top10:
                        if get_balance(tkr,"KRW") > 5000:
                            sell(tkr)
                            num_sell += 1
                        time.sleep(0.1)
        # 잔고 Update
            balanceBackup = totalBalance
            totalBalance = get_totalKRW()
            if fStart == 0:
                balanceBackup = totalBalance
                fStart = 1
            balance = totalBalance / 10
            balChange = totalBalance - balanceBackup
            balChngPercent = balChange / balanceBackup * 100
        # 1시간 매매 결과 송신
            post_message(myToken, myChannel, "=== "+str(timeBackup)+"시 ~ "+str(now.hour)+"시 매매 결과 ===")
            post_message(myToken, myChannel, " - 매수 : "+str(num_buy)+"회, 매도 : "+str(num_sell)+"회")
            post_message(myToken, myChannel, " - 시작 잔고 : "+str(round(balanceBackup))+"원")
            post_message(myToken, myChannel, " - 종료 잔고 : "+str(round(totalBalance))+"원")
            post_message(myToken, myChannel, " - 수익 : "+str(round(balChange))+"원 ("+str(round(balChngPercent, 2))+"%)")
            num_buy = num_sell = 0
            timeBackup = now.hour


    # 매매 logic
        for i in range(0, 10):
            tkr = tkr_top10[i]
            # 매수
            if (get_balance(tkr_top10[i],"KRW") < 5000) and balance > 5000:
                current = get_current_price(tkr)
                # 목표가보다 상승 시 매수
                if current > buy_price[i]:
                    buy(tkr, balance)
                    num_buy += 1
            # 매도
            elif get_balance(tkr_top10[i],"KRW") > 5000:
                current = get_current_price(tkr)
                # 전 시간 종가보다 하락 시 매도
                if current < sell_price[i]:
                    sell(tkr)
                    num_sell += 1
            time.sleep(0.1)
        time.sleep(1)      
        

    except Exception as e:
        print(e)
        post_message(myToken, myChannel, e)
        time.sleep(1)
