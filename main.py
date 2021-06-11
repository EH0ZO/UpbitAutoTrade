from vars_funcs import *

# Main Logic
minBack = -1
startBalance = hourlyBalance = get_totalKRW()
time.sleep(0.1)
# 시작 메세지 슬랙 전송
txt = "==================================\n"
txt+= "autotrade start (ver."+VERSION+"))\n"
txt+= str(datetime.datetime.now())+"\n"
txt+= "=================================="
send(txt)

while True:
    try:
        now = datetime.datetime.now()
    # 매시간
        if timeBackup != now.hour or fStart == 0:
        # 1시간 매매 결과 송신
            curBalance = get_totalKRW()
            balance = (curBalance / tkr_num) *0.9
            num_buy_total += num_buy
            num_sell_total += num_sell
            # 수익 계산
            balChange_hr = curBalance - hourlyBalance
            balChngPercent_hr = balChange_hr / hourlyBalance * 100
            balChange_d = curBalance - startBalance
            balChngPercent_d = balChange_d / startBalance * 100
            hourlyBalance = curBalance
            # 결과 송신
            txt = "=== Hourly Report ===\n"
            txt+= " - 현재 잔고  : "+str(round(curBalance))+"원\n"
            txt+= " - 매수(시간) : "+str(num_buy)+"회, 매도(시간) : "+str(num_sell)+"회\n"
            txt+= " - 매수(금일) : "+str(num_buy_total)+"회, 매도(금일) : "+str(num_sell_total)+"회\n"
            txt+= " - 수익(시간) : "+str(round(balChange_hr))+"원 ("+str(round(balChngPercent_hr, 2))+"%)\n"
            txt+= " - 수익(금일) : "+str(round(balChange_d))+"원 ("+str(round(balChngPercent_d, 2))+"%)"
            send(txt)
            hourlyBalance = curBalance
            num_buy = num_sell = 0
            # RSI 값 송신
            txt = "=== RSI14 Value ===\n"
            for i in range(0,tkr_num):
                if rsi14[i] == 0:
                    rsi14[i] = get_rsi14(tkr_buy[i], rsi_intv)
                txt += tkr_buy[i]+" : "+str(round(rsr_h_avg[i],1))+"/"+str(round(rsi14[i],1))+"/"+str(round(rsr_l_avg[i],1))+"\n"
        # 매일 09시 Reset
            if fStart == 0 or now.hour == 9:           
                num_buy_total = num_sell_total = 0
                for i in range(0,tkr_num):
                    rsr_l_sum[i] = 30 + rsr_l_avg[i] * rsr_l_cnt_d[i]
                    rsr_l_cnt[i] = rsr_l_cnt_d[i] + 1
                    rsr_l_cnt_d[i] = 0
                    rsr_l_avg[i] = rsr_l_sum[i] / rsr_l_cnt[i]
                    rsr_h_sum[i] = 70 + rsr_h_avg[i] * rsr_h_cnt_d[i]
                    rsr_h_cnt[i] = rsr_h_cnt_d[i] + 1
                    rsr_h_cnt_d[i] = 0
                    rsr_h_avg[i] = rsr_h_sum[i] / rsr_h_cnt[i]
            # 탈락 종목 전량 매도
                sell_not_in()
            # 잔고 Update
                startBalance = hourlyBalance = get_totalKRW()
                fStart = 1
            timeBackup = now.hour
    # 매매 logic
        if minBack != now.minute:
            for i in range(0, tkr_num):
                tkr = tkr_buy[i]
                balanceDiff = balance - get_balance(tkr,"KRW")
                rsi14[i] = get_rsi14(tkr, rsi_intv)
                # rsi 하방 check
                if rsi14[i] < rsr_l_avg[i]:
                    f_rsi_l[i] = 1
                if f_rsi_l[i] == 1 and rsi14[i] > rsr_l_avg[i]:
                    f_rsi_l[i] = 2
                # rsi 상방 check
                if rsi14[i] > rsr_h_avg[i]:
                    f_rsi_h[i] = 1
                if f_rsi_h[i] == 1 and rsi14[i] < rsr_h_avg[i]:
                    f_rsi_h[i] = 2
                send_rsi(i)
            # 매수 : rsi low 미만 -> 초과 시
                if f_rsi_l[i] == 2:
                    krw = get_krw()
                    tkr_balance = get_balance(tkr, "KRW")
                    total_krw = get_totalKRW()
                    if tkr_balance < (total_krw/tkr_num) and krw > 5000:
                        current = get_current_price(tkr)
                        if krw - 10000 < 5000:
                            buy(tkr, krw)
                        else:
                            buy(tkr, 10000)
                        num_buy += 1
                        send(tkr+" 매수 (rsi: "+str(round(rsi14[i]))+", 가격: "+str(round(current)))
                    f_rsi_l[i] = 0
            # 매도 : rsi 70 초과 -> 미만 시
                if f_rsi_h[i] == 2:
                    krw = get_krw()
                    tkr_balance = get_balance(tkr, "KRW")
                    total_krw = get_totalKRW()
                    if tkr_balance > 5000:
                        current = get_current_price(tkr)
                        if tkr_balance - 10000 < 5000:
                            sell(tkr, 0)
                        else:
                            sell(tkr, 10000)
                        num_sell += 1
                        send(tkr+" 매도 (rsi: "+str(round(rsi14[i]))+", 가격: "+str(round(current)))
                    f_rsi_h[i] = 0
                calc_rsi_avg(i)
                rsi14_back[i] = rsi14[i]
                time.sleep(0.1)
            minBack = now.minute
            
            
    except Exception as e:
        print(e)
        send(e)
        time.sleep(1)
