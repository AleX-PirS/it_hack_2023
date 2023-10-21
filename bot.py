import telebot
import regex
from threading import Thread
import whisper
from pytube import YouTube
import time
import os
from dotenv import load_dotenv

class Service(object):
    # youtube query
    youtybe_reg = "https:\/\/www\.youtube\.com\/watch\?v="
    # folder with temporary files
    youtybe_location = "/temp/"
    # max length of text message in telegram
    max_length=4000
    # whisper model
    ml_model = "small"

    def __init__(self) -> None:
        load_dotenv()

        try:
            self.hugging_face_token = os.getenv("HUGGING_FACE_TOKEN")
            if self.hugging_face_token is None: raise
            self.tg_bot_token = os.getenv("TG_BOT_TOKEN")
            if self.tg_bot_token is None: raise
        except:
            self.logging("invalid .env data")
            os._exit(0)

        self.bot = telebot.TeleBot(self.tg_bot_token)

        @self.bot.message_handler(func=lambda message: True)
        def _linker(message:telebot.types.Message):
            self.linker(message)
    
    def linker(self, message:telebot.types.Message):
        if len(regex.findall(self.youtybe_reg, message.text)) == 0:
            self.bot.send_message(message.chat.id, f'{message.from_user.first_name}, необходима ссылка на YouTube!')
            return
        
        Thread(target=self.analyse_text, args=(message, )).start()
        return 

    def polling_bot(self):
        self.bot.polling()

    def analyse_text(self, message:telebot.types.Message):
        self.logging(f"Get new analyse request: username:https://t.me/{message.from_user.username}, url:{message.text}")
        start_time = time.time()
        yt = YouTube(message.text)

        try:
            fn = yt.streams.filter(type="audio")[0].download(self.youtybe_location)
        except Exception as e:
            self.bot.send_message(message.chat.id, f'Error download video: {e}')
            return

        model = whisper.load_model(self.ml_model)
        res = model.transcribe(fn)

        print(res)

        print(f'Time duration: {time.time()-start_time} for video length {yt.length} seconds. Speed={yt.length/(time.time()-start_time)}')

        text = res["text"]

        parts = []
        if len(text) <= self.max_length:
            self.send_chanks(message.chat.id, [text])
        else:
            for i in range(0, len(text), self.max_length):
                parts.append(text[i:i + self.max_length])
                
            self.send_chanks(message.chat.id, parts)

    def logging(self, mes:str):
        print(mes)

    def send_chanks(self, id, chanks):
        for i in chanks:
            self.bot.send_message(id, i)

    def start_app(self):
        Thread(target=self.polling_bot).start()

if __name__ == "__main__":
    app = Service()
    app.start_app()
    