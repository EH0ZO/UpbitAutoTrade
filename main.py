from vars_funcs import *

# Main Logic
trade_intv = 3          # trade_intv 분 주기로 매매 감시
intv = 4                # intv 시간 candle 참조
intv_s = "minute240"
fStart = timeBackup = num_buy = num_sell = minBack = hrBack = 0
startBalance = hourlyBalance = get_totalKRW()
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
            send_hour_report(curBalance)
        # 매일 09시 Reset
            if fStart == 0 or now.hour == 9:           
                num_buy_total = num_sell_total = 0
                buy_n_hold_start(curBalance)
                for i in range(0,tkr_num):
                    target_price[i] = get_open_price(tkr_buy[i], intv_s)
            # 탈락 종목 전량 매도
                sell_not_in()
            # 잔고 Update
                startBalance = hourlyBalance = get_totalKRW()
                fStart = 1
            timeBackup = now.hour

    # 매매 logic
        if (minBack != now.minute) and (now.minute % trade_intv == 0):
            for i in range(0, tkr_num):
                tkr = tkr_buy[i]
                balanceDiff = balance - get_balance(tkr,"KRW")
                if isNewCandle(intv, now) == True and now.minute < 5:
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
