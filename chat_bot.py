from vars_funcs import *
from telegram.ext import Updater, MessageHandler, Filters

def chat(update, context):
    global last_rx_time, unit_trade_price, rsi_l_std, rsi_h_std, stop_loss, confirm_sell, confirm_quit, trade_intv, rsi_intv
    new_text = update.message.text
    if new_text != None:
        if new_text[0] == "1":
            send_hourly_report(0)
        elif new_text[0] == "2":
            if len(new_text) < 4:
                send("wrong input")
            elif not('0' <= new_text[3] <= '9'):
                send("wrong input")
            else:
                num = float(new_text[3:])
                if num > 5000:
                    unit_trade_price = num
                    send("unit_trade_price changed : "+str(unit_trade_price))
                else:
                    send("wrong input")
        elif new_text[0] == "3":
            if len(new_text) < 4: 
                send("wrong input")
            elif not('0' <= new_text[3] <= '9'):
                send("wrong input")
            else:
                num = float(new_text[3:])
                if 0 < num < 60:
                    trade_intv = int(num)
                    send("trade_intv changed : "+str(trade_intv))
                else:
                    send("wrong input")
        elif new_text[0] == "4":
            if len(new_text) < 4:
                send("wrong input")
            elif not('0' <= new_text[3] <= '9'):
                send("wrong input")
            else:
                num = float(new_text[3:])
                if 0 < num <= 240:
                    rsi_intv = int(num)
                    send("rsi_intv changed : "+str(rsi_intv))
                else:
                    send("wrong input")
        elif new_text[0] == "5":
            if len(new_text) < 4: 
                send("wrong input")
            elif not('0' <= new_text[3] <= '9'):
                send("wrong input")
            else:
                num = float(new_text[3:])
                if 50 < num < 100:
                    rsi_h_std = num
                    send("rsi_h_std changed : "+str(rsi_h_std))
                else:
                    send("wrong input")
        elif new_text[0] == "6":
            if len(new_text) < 4: 
                send("wrong input")
            elif not('0' <= new_text[3] <= '9'):
                send("wrong input")
            else:
                num = float(new_text[3:])
                if 0 < num < 50:
                    rsi_l_std = num
                    send("rsi_l_std changed : "+str(rsi_l_std))
                else:
                    send("wrong input")
        elif new_text[0] == "7":
            if len(new_text) < 4: 
                send("wrong input")
            elif not('0' <= new_text[3] <= '9'):
                send("wrong input")
            else:
                num = float(new_text[3:])
                if 0 < num < 1:
                    stop_loss = num
                    send("stop_loss changed : "+str(stop_loss))
                else:
                    send("wrong input")
        elif new_text[0] == "8":
            reset_rsi_std()
            send("reset rsi std")
        elif new_text[0] == "9":
            txt = "unit_trade_price : "+str(unit_trade_price)+"\n"
            txt+= "trade_intv       : "+str(trade_intv)+"\n"
            txt+= "rsi_intv         : "+str(rsi_intv)+"\n"
            txt+= "rsi_h_std        : "+str(rsi_h_std)+"\n"
            txt+= "rsi_l_std        : "+str(rsi_l_std)+"\n"
            txt+= "stop_loss        : "+str(stop_loss)+"\n"
            txt+= "pg version        : "+VERSION
            send(txt)
        elif new_text == "sell":
            confirm_sell = 1
            txt = "보유종목을 전량 매도합니다.\n"
            txt+= "진행하시겠습니까? (yes/no)"
            send(txt)
        elif new_text == "quit":
            confirm_quit = 1
            txt = "프로그램을 종료합니다.\n"
            txt+= "진행하시겠습니까? (yes/no)"
            send(txt)
        elif confirm_sell == 1:
            if new_text == "yes":
                confirm_sell = 0
                send("보유종목을 전량 매도합니다.")
                sell_all()
            else:
                confirm_sell = 0
                send("취소합니다.")
        elif confirm_quit == 1:
            if new_text == "yes":
                send("프로그램을 종료합니다.")
                sys.exit()
            else:
                confirm_quit = 0
                send("취소합니다.")
        else:
            txt = "========== Menu ==========\n"
            txt+= "1    : 현재 상태 출력\n"
            txt+= "2, N : unit_trade_price N으로 변경\n"
            txt+= "3, N : trade_intv N으로 변경\n"
            txt+= "4, N : rsi_intv N으로 변경\n"
            txt+= "5, N : rsi_h_std N으로 변경\n"
            txt+= "6, N : rsi_l_std N으로 변경\n"
            txt+= "7, N : stop_loss N으로 변경\n"
            txt+= "8    : reset rsi std\n"
            txt+= "9    : 현재 parameter 값 확인\n"
            txt+= "sell : 전량 매도\n"
            txt+= "quit : 프로그램 종료"
            send(txt)

updater = Updater(token, use_context=True)
msg_handler = MessageHandler(Filters.text, chat)
updater.dispatcher.add_handler(msg_handler)
