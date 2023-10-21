import telebot
import regex
from threading import Thread
import whisper
from pytube import YouTube

youtybe_reg = "https:\/\/www\.youtube\.com\/watch\?v="

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
    yt = YouTube(message.text)
    fn = yt.streams.filter(type="audio")[0].download()

    model = whisper.load_model("small")
    res = model.transcribe(fn)

    bot.send_message(message.chat.id, res["text"])

if __name__ == "__main__":
    Thread(target=polling_bot).start()
    