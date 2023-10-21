import telebot
import regex
from threading import Thread
import whisper
from pytube import YouTube
import time

youtybe_reg = "https:\/\/www\.youtube\.com\/watch\?v="
youtybe_location = "/temp"

max_length=100

bot = telebot.TeleBot('6487666443:AAFUZhjk4nbrRMaI6G8D5_BiyXqHnoW-wqU')

@bot.message_handler(func=lambda message: True)
def linker(message:telebot.types.Message):
    if len(regex.findall(youtybe_reg, message.text)) == 0:
        bot.send_message(message.chat.id, f'{message.from_user.first_name}, необходима ссылка на YouTube!')
        return
    
    Thread(target=analyse_text, args=(message, )).start()
    return    

def polling_bot():
    bot.polling()

def analyse_text(message:telebot.types.Message):
    start_time = time.localtime()
    yt = YouTube(message.text)
    fn = yt.streams.filter(type="audio")[0].download(youtybe_location)

    model = whisper.load_model("tiny")
    res = model.transcribe(fn)

    text = res["text"]

    parts = []
    if len(text) <= max_length:
        parts.append(text)
    else:
        for i in range(0, len(text), max_length):
            parts.append(text[i:i + max_length])
            print(text[i:i + max_length], '\n\n')

    for i in parts:  
        bot.send_message(message.chat.id, res["text"])

    stop_time = time.localtime()

    print(f'Data about: {stop_time-start_time}')  

if __name__ == "__main__":
    Thread(target=polling_bot).start()
    