from vars_funcs import *
# Main Logic
# 시작 메시지 전송
while True:
    fError = 0
    send_start_message()
    restore()

    while True:
        try:
            chk = check_chatbot("set")
            if check_restart() == 1:
                backup()
                reset_newday()
                reset_rsi_std()
                break;
            now = datetime.datetime.now()
        # 매매 logic
            if (min_backup != now.minute) and (now.minute % trade_intv == 0):
                for i in range(0, tkr_num):
                    check_rsi(i)
                    calc_rsi_avg(i)
                    trade(i)
            elif chk < 10:
                updater.start_polling(timeout=3, drop_pending_updates=True)
                updater.idle
        # 매시간
            if time_backup != now.hour or f_start == 0:
            # 1시간 매매 결과 송신
                send_hourly_report(1)
            # 매일 09시 Reset
                if f_start == 0 or now.hour == 9:           
                    reset_newday()
                    f_start = 1
                time_backup = now.hour
            min_backup = now.minute
            time.sleep(1)
            check_chatbot("clear")
            if fError > 0:
                fError = 0
                send("error cleared")
                
        except Exception as e:
            if fError < 5:
                fError += 1
                send("error ocurred")
            send(e)
            time.sleep(1)
