import telebot
import regex
from threading import Thread
import whisper
from pytube import YouTube
import time
import os
from dotenv import load_dotenv
from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
from random import uniform
import numpy as np

class Person(object):
    id = 0.0
    start_time = 0
    stop_time = 0
    text = ""

    def __init__(self, id, start_time, stop_time, text) -> None:
        self.id = id
        self.text = text
        self.start_time = start_time
        self.stop_time = stop_time
    
    def get_id(self):
        return self.id
    
    def get_start_time(self):
        return self.start_time
    
    def get_stop_time(self):
        return self.stop_time
    
    def get_name(self):
        return self.name
    
    def get_text(self):
        return self.text
    
    def change_stop_time(self, time):
        self.stop_time = time

    def add_text(self, text:str):
        self.text += text

class Meeting(object):
    def __init__(self, accuracy, data, lenght) -> None:
        self.persons = dict()
        self.timeline = dict()
        self.last_person_id = -1
        self.personal_frames = [Person]

        self.create_list_persons(data)

        for i in np.arange(0, lenght+1, accuracy):
            i = round(float(i), 1)
            # key: time, val: id of pers
            for j in range(len(data)):
                frame = data[j]
                if self.is_in_interval(frame[0], frame[1], i):
                    self.timeline[i] = frame[2]
                    break
                if j == (len(data)-1):
                    self.timeline[i] = frame[2]
                continue
    
    def add_personal_frame(self, person:Person):
        self.personal_frames.append(person)
    
    def change_last_person_stop_time_and_text(self, time, text):
        self.personal_frames[-1].change_stop_time(time)
        self.personal_frames[-1].add_text(text)

    def create_list_persons(self, data):
        for frame in data:
            self.add_person(Person(id=frame[2], start_time=0, stop_time=0, text=""))

    def is_in_interval(self, a, b, i):
        return (a<=i) & (i<b)

    def add_person(self, pers:Person):
        if pers.get_id in self.persons.keys():
            return
        self.persons[pers.get_id] = pers

class Service(object):
    # discreteness
    accuracy = 0.1

    # youtube query
    youtybe_reg = "https:\/\/www\.youtube\.com\/watch\?v="
    rttm_req = "SPEAKER \S* 1 ([0-9\.]*) ([0-9\.]*) <NA> <NA> SPEAKER_([0-9]*) <NA> <NA>\n"

    # folder with temporary files
    abs_path = os.path.dirname(os.path.abspath(__file__))
    temp_location = abs_path + r'\temp'
    res_location = abs_path + r'\result\\'  

    # max length of text message in telegram
    max_length=4000
    max_video_length = 120

    # Models
    ml_model = "medium"
    di_model = "pyannote/speaker-diarization-3.0"

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
        self.bot.infinity_polling(timeout=10, long_polling_timeout=5)

    def analyse_text(self, message:telebot.types.Message):
        factor = (1 + uniform(0, 0.3)) * 2.1
        self.logging(f"Get new analyse request: username:https://t.me/{message.from_user.username}, url:{message.text}")
        yt = YouTube(message.text)

        if yt.length > self.max_video_length:
            self.bot.send_message(message.chat.id, f'{message.from_user.first_name}, видео должно быть не более 2 минут!')
            return

        self.bot.send_message(message.chat.id, f'Приблизительное время составления протокола: {round(yt.length*factor, 2)} сек')

        try:
            try:
                fn = yt.streams.filter(type="audio")[1].download(output_path=self.temp_location)
            except:
                fn = yt.streams.filter(type="audio")[0].download(output_path=self.temp_location)
            os.system(f'ffmpeg -i "{fn}" -acodec pcm_s16le -ar 16000 {fn[:fn.rfind(".")].replace(" ", "_")}.wav')
            fn, fnold = fn[:fn.rfind(".")].replace(" ", "_") + ".wav", fn
            # fn_wav, fn_rttm = fn+".wav", fn+".rttm"
            os.remove(fnold)
        except Exception as e:
            self.bot.send_message(message.chat.id, f'Error download video: {e}')
            return
        
        trans = self.transcript(fn)
        diar = self.diarization(fn, yt.length)
        result = self.summarize(trans, diar)

        for fr in result.personal_frames:
            if fr.text == "":
                continue
            text_data = f'*Person:* №{fr.id}. *Time* {fr.start_time}-{fr.stop_time} сек\n_{fr.text}_'
            self.send_chanks(message.chat.id, [text_data])

    def transcript(self, fn):
        model = whisper.load_model(self.ml_model)
        return model.transcribe(fn)

    def send_text(self, text, message):
        parts = []
        if len(text) <= self.max_length:
            self.send_chanks(message.chat.id, [text])
        else:
            for i in range(0, len(text), self.max_length):
                parts.append(text[i:i + self.max_length])
                
            self.send_chanks(message.chat.id, parts)

    def diarization(self, fn, lengh):
        pipeline = Pipeline.from_pretrained(self.di_model, use_auth_token=self.hugging_face_token)

        diarization = pipeline(fn)

        data = regex.findall(self.rttm_req, diarization.to_rttm())

        for i in range(len(data)):
            if i==0:
                data[i] = (0.0, float(data[i][0])+float(data[i][1]), float(data[i][2]))
                continue
            if i == (len(data)-1):
                data[i] = (float(data[i][0]), lengh, float(data[i][2]))
                continue
            data[i] = (float(data[i][0]), float(data[i][0])+float(data[i][1]), float(data[i][2]))

        meeting = Meeting(self.accuracy, data, lengh)

        os.remove(fn)
        return meeting

    def summarize(self, whisper, meeting:Meeting):
        for segment in whisper["segments"]:
            start_time=segment['start']
            stop_time=segment['end']
            text=segment['text']
            id = meeting.timeline[round((stop_time+start_time)/2, 1)]
            
            if id == meeting.last_person_id:
                meeting.change_last_person_stop_time_and_text(text=text, time=stop_time)
                continue

            meeting.add_personal_frame(Person(start_time=start_time, stop_time=stop_time, id=id, text=text))
            meeting.last_person_id = id
        
        return meeting

    def logging(self, mes:str):
        print(mes)

    def send_chanks(self, id, chanks):
        for i in chanks:
            self.bot.send_message(id, i, parse_mode='Markdown')

    def start_app(self):
        Thread(target=self.polling_bot).start()

if __name__ == "__main__":
    app = Service()
    app.start_app()
    