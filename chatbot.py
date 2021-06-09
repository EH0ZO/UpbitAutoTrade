import telegram

# Global variables

# Keys
token = "1814838763:AAGNuB_LWtq8zJMHuezB-vsSI8C4b9X9QLk"
chat_id = 1883488213
bot = telegram.Bot(token)

# Text
menu = (
"-menu-\n"
"1. current setting\n"
"2. change setting\n"
"9. exit"

# Functions
def send(txt):
    # 텔레그램 메시지 전송
    bot.sendMessage(chat_id, txt)        
    
def chatbot(t_back):
    recent = bot.getUpdates()[-1].message
    time = recent.date
    if time != t_back:
