import telegram




def chatbot(t_back):
    recent = bot.getUpdates()[-1].message
    time = recent.date
    if time != t_back:
