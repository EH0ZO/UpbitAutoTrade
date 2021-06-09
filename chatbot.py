import telegram

# Global variables
cur_page = 0

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
    "2. get current \n"
    "9. exit")
    send(txt)

# page no.11
def send_settings():
    txt = (
    "current settings\n"
    "  intv : "+str(intv)+"\n"
    "  intv : "+str(intv)+"\n"
    "  intv : "+str(intv)+"\n"
    "  intv : "+str(intv)+"\n"
    "0. back\n"
    "1. change settings\n"
    "9. exit")

# page no.111
chg_settings = (
"0. back\n"
"1. current setting\n"
"2. change setting\n"
"9. exit")

# Functions
def send(txt):
    # 텔레그램 메시지 전송
    bot.sendMessage(chat_id, txt)        
    
def chatbot(t_back):
    recent = bot.getUpdates()[-1].message
    time = recent.date
    if time != t_back:
