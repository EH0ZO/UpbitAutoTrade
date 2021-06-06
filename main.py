from vars_funcs import *

# Main Logic
trade_intv = 1          # trade_intv 분 주기로 매매 감시
intv = 4                # intv 시간 candle 참조
intv_s = "minute240"
fStart = timeBackup = num_buy = num_sell = minBack = hrBack = 0
startBalance = hourlyBalance = get_totalKRW()
time.sleep(0.1)
buy_n_hold = buy_n_hold_start(startBalance)
time.sleep(0.1)
# 시작 메세지 슬랙 전송
post_message(myToken, myChannel, "==================================")
post_message(myToken, myChannel, "autotrade start (ver."+VERSION+"))")
post_message(myToken, myChannel, str(datetime.datetime.now()))
post_message(myToken, myChannel, "==================================")

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
            bnhBalance = 0
            for i in range(0,tkr_num):
                price = get_current_price(tkr_buy[i])
                bnhBalance += buy_n_hold[i] * price
            balChange_d_bnh = bnhBalance - startBalance
            balChngPercent_d_bnh = balChange_d_bnh / startBalance * 100
            hourlyBalance = curBalance
            # 결과 송신
            post_message(myToken, myChannel, "=== Hourly Report ===")
            post_message(myToken, myChannel, " - 현재 잔고  : "+str(round(curBalance))+"원")
            post_message(myToken, myChannel, " - 매수(시간) : "+str(num_buy)+"회, 매도(시간) : "+str(num_sell)+"회")
            post_message(myToken, myChannel, " - 매수(금일) : "+str(num_buy_total)+"회, 매도(금일) : "+str(num_sell_total)+"회")
            post_message(myToken, myChannel, " - 수익(시간) : "+str(round(balChange_hr))+"원 ("+str(round(balChngPercent_hr, 2))+"%)")
            post_message(myToken, myChannel, " - 수익(금일) : "+str(round(balChange_d))+"원 ("+str(round(balChngPercent_d, 2))+"%)")
            post_message(myToken, myChannel, " - 수익(존버) : "+str(round(balChange_d_bnh))+"원 ("+str(round(balChngPercent_d_bnh, 2))+"%)")
            hourlyBalance = curBalance
            num_buy = num_sell = 0
        # 매일 09시 Reset
            if fStart == 0 or now.hour == 9:           
                num_buy_total = num_sell_total = 0
                for i in range(0,tkr_num):
                    target_price[i] = get_open_price(tkr_buy[i], intv_s)
            # 탈락 종목 전량 매도
                sell_not_in()
            # 잔고 Update
                startBalance = hourlyBalance = get_totalKRW()
                buy_n_hold = buy_n_hold_start(curBalance)
                fStart = 1
            timeBackup = now.hour

    # 매매 logic
        if (minBack != now.minute) and (now.minute % trade_intv == 0):
            for i in range(0, tkr_num):
                tkr = tkr_buy[i]
                balanceDiff = balance - get_balance(tkr,"KRW")
                if isNewCandle(intv, now) == True and now.minute < (trade_intv * 3):
                    target_price[i] = get_open_price(tkr_buy[i], intv_s)
            # 매수
                if balanceDiff > 5000:
                    current = get_current_price(tkr)
                    if current > (target_price[i] + tick(current)) and ((current-target_price[i]) / target_price[i]) < 0.02:
                        buy(tkr, balanceDiff)
                        num_buy += 1
            # 매도
                elif get_balance(tkr_buy[i],"KRW") > 5000:
                    current = get_current_price(tkr)
                    if current < (target_price[i] - tick(current)):
                        sell(tkr)
                        num_sell += 1
                time.sleep(0.1)
            minBack = now.minute

    except Exception as e:
        print(e)
        post_message(myToken, myChannel, e)
        time.sleep(1)
