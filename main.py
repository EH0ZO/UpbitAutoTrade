from vars_funcs import *
# Main Logic

# 로그인
fStart = fSelect = fSend = 0
# 시작 메세지 슬랙 전송
post_message(myToken, myChannel, "==================================")
post_message(myToken, myChannel, "autotrade start (ver."+VERSION+"))")

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)

        # 최초 시작 시 종목 선정
        if fStart == 0:
            select_tkrs()
            fSend = 0
            fStart = 1
        # 6시간마다 종목 갱신
        elif now.hour % 6 == 0:
            if fSelect == 0:
                select_tkrs()
                for i in range(0,20):
                    if tkr_top20[i] not in tkr_top20_new and get_balance(tkr_top20[i],"KRW") > 5000:
                        sell(tkr_top20[i])
                        time.sleep(0.5)
                tkr_top20 = tkr_top20_new
                fSend = 0
                fSelect = 1
        else:
            fSelect = 0
        
        if fSend == 0:
            print(tkr_top20)
            post_message(myToken, myChannel, "종목 선정 완료 : "+str(datetime.datetime.now()))
            post_message(myToken, myChannel, str(tkr_top20))
            fSend = 1


        for i in range(0, 20):
            tkr = tkr_top20[i]
            K = 0.0005 # 0.05%
            # 매수 감시 : (60분 평균가 > 180분 평균가*1.0005) && (현재가 > 60분 평균가*1.0005)
            if (get_balance(tkr_top20[i],"KRW") < 5000) and balance > 5000:
                min_avg_60 = get_min_avg(tkr, 60)
                min_avg_180 = get_min_avg(tkr, 180)
                current = get_current_price(tkr)
                if (min_avg_60 > min_avg_180*(1+K))) and (current > min_avg_60*(1+K)):
                    buy(tkr)
            # 매도 감시 : (60분 평균가 < 180분 평균가*0.9995) && (현재가 < 60분 평균가*0.9995)
            if get_balance(tkr_top20[i],"KRW") > 5000:
                min_avg_60 = get_min_avg(tkr, 60)
                min_avg_180 = get_min_avg(tkr, 180)
                current = get_current_price(tkr)
                if (min_avg_60 < min_avg_180*(1-K)) or (current < min_avg_60*(1-K)):
                    sell(tkr)
            time.sleep(0.5)
        time.sleep(1)

    except Exception as e:
        print(e)
        post_message(myToken, myChannel, e)
        time.sleep(1)
