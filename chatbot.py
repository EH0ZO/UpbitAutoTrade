import telegram
from vars_funcs import *

# Global variables
cur_page = 0
t_back = 0

# Keys
token = "1814838763:AAGNuB_LWtq8zJMHuezB-vsSI8C4b9X9QLk"
chat_id = 1883488213
bot = telegram.Bot(token)

# Text
# page no.1
def send_menu():
    txt = (
    "== menu ==\n"
    "1. settings\n"
    "2. get current status\n"
    "9. exit")
    send(txt)

# page no.11
def send_settings(intv, u_band, l_band, trade_intv):
    txt = (
    "current settings\n"
    "  candle : "+str(intv)+"\n"
    "  upper band : "+str(u_band)+"\n"
    "  lower band : "+str(l_band)+"\n"
    "  trading interval : "+str(trade_intv)+"\n\n"
    "0. back\n"
    "1. change settings\n"
    "9. exit")
    send(txt)

# page no.111
def send_chg_settings():
    txt = (
    "0. back\n"
    "1. current setting\n"
    "2. change setting\n"
    "9. exit")
    send(txt)

# page no.12
def send_current_status():
    txt = (
    "0. back\n"
    "1. current setting\n"
    "2. change setting\n"
    "9. exit")
    send(txt)


# Functions
def send(txt):
    # 텔레그램 메시지 전송
    bot.sendMessage(chat_id, txt)        
    
def chatbot():
    global t_back
    recent = bot.getUpdates()[-1].message
    time = recent.date
    txt = recent.text
    if time != t_back:
        t_back = time
        if txt == "menu":
            send_menu()
        else:
        
