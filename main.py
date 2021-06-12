from vars_funcs import *

# Main Logic
startBalance = hourlyBalance = get_totalKRW()
# 시작 메시지 전송
send_start_message()

while True:
    try:
        now = datetime.datetime.now()
    # 매시간
        if time_backup != now.hour or f_start == 0:
        # 1시간 매매 결과 송신
            send_hourly_report(1)
        # 매일 09시 Reset
            if f_start == 0 or now.hour == 9:           
                reset_newday()
                f_start = 1
            time_backup = now.hour
    # 매매 logic
        if min_backup != now.minute:
            for i in range(0, tkr_num):
                check_rsi(i)
                calc_rsi_avg(i)
                trade(i)
                time.sleep(0.1)
            check_message()
            min_backup = now.minute
            
    except Exception as e:
        send(e)
        time.sleep(1)
