from vars_funcs import *
# Main Logic

# 로그인
fStart = timeBackup = 0
# 시작 메세지 슬랙 전송
post_message(myToken, myChannel, "==================================")
post_message(myToken, myChannel, "autotrade start (ver."+VERSION+"))")
post_message(myToken, myChannel, "==================================")

while True:
    try:
        now = datetime.datetime.now()

    # 1시간 마다 신규 종목 선정
        if(timeBackup != now.hour):
        # 기존 종목 전량 매도
            post_message(myToken, myChannel, "=== 전량 매도 : "+str(datetime.datetime.now()))
            balances = upbit.get_balances()
            time.sleep(0.1)
            for b in balances:
                if b['currency'] != 'KRW':
                    tkr = "KRW-"+b['currency']
                    if get_balance(tkr,"KRW") > 5000:
                        sell(tkr)
                    time.sleep(0.1)

        # 잔고 Update
            balanceBackup = totalBalance
            totalBalance = get_krw()
            if fStart == 0:
                balanceBackup = totalBalance
                fStart = 1
            balance = totalBalance / 10
            balChange = totalBalance - balanceBackup
            balChngPercent = balChange / balanceBackup * 100

        # 1시간 매매 결과 송신
            post_message(myToken, myChannel, "=== "+str(timeBackup)"시 ~ "+str(now.hour)"시 매매 결과 ===")
            post_message(myToken, myChannel, " - 시작 잔고 : "+str(round(balanceBackup))+"원")
            post_message(myToken, myChannel, " - 종료 잔고 : "+str(round(totalBalance))+"원")
            post_message(myToken, myChannel, " - 수익 : "+str(round(balChange))+"원 ("+str(round(balChngPercent), 2)+"%)")

        # 신규 종목 선정 및 목표가 계산
            post_message(myToken, myChannel, "=== 종목 선정 시작 : "+str(datetime.datetime.now()))
            tkr_top10 = select_tkrs()
            for i in range(0,10):
                # 목표가 : 전 시간 종가 + (전 시간 고점 - 저점) * K
                ret = get_target_close_prce(tkr_top10[i])
                target_price[i] = ret[0]
                close_price[i] = ret[1]
                time.sleep(0.1)
            post_message(myToken, myChannel, "=== 종목 선정 완료 : "+str(datetime.datetime.now()))
            post_message(myToken, myChannel, str(tkr_top10))

            timeBackup = now.hour


    # 매매 logic
        for i in range(0, 10):
            tkr = tkr_top10[i]
            # 매수
            if (get_balance(tkr_top10[i],"KRW") < 5000) and balance > 5000:
                current = get_current_price(tkr)
                # 목표가보다 상승 시 매수
                if current >= target_price[i]:
                    buy(tkr, balance)
            # 매도
            elif get_balance(tkr_top10[i],"KRW") > 5000:
                current = get_current_price(tkr)
                # 전 시간 종가대비 -1% 하락 시 매도
                if current < (close_price[i] * (0.99)):
                    sell(tkr)
            time.sleep(0.1)
        time.sleep(1)      
        

    except Exception as e:
        print(e)
        post_message(myToken, myChannel, e)
        time.sleep(1)