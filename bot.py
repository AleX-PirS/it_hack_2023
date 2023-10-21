import telebot
import regex
from threading import Thread
import whisper
from pytube import YouTube
import time

youtybe_reg = "https:\/\/www\.youtube\.com\/watch\?v="
youtybe_location = "/temp/"

max_length=4000

ml_model = "small"

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
    logging(f"Get new analyse request: username:https://t.me/{message.from_user.username}, url:{message.text}")
    start_time = time.time()
    yt = YouTube(message.text)

    try:
        fn = yt.streams.filter(type="audio")[0].download(youtybe_location)
    except Exception as e:
        bot.send_message(message.chat.id, f'Error download video: {e}')
        return

    model = whisper.load_model(ml_model)
    res = model.transcribe(fn)

    print(res)

    print(f'Time duration: {time.time()-start_time} for video length {yt.length} seconds. Speed={yt.length/(time.time()-start_time)}')

    text = res["text"]

    parts = []
    if len(text) <= max_length:
        send_chanks(message.chat.id, [text])
    else:
        for i in range(0, len(text), max_length):
            parts.append(text[i:i + max_length])
            
        send_chanks(message.chat.id, parts)

def logging(mes:str):
    print(mes)

def send_chanks(id, chanks):
    for i in chanks:
        bot.send_message(id, i)

if __name__ == "__main__":
    Thread(target=polling_bot).start()
    