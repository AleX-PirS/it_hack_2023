# Цифровой стенографист

____

![Approach](https://uadoc.com.ua/img/stenograf.jpg )


## Описание

____


Этот репозиторий обеспечивает автоматическое распознование речи _с помощью различных моделей_ с проставлением временных меток и разделением спикеров. Наше решение использует одновременно несколько нейросетей для корректного выполнения технического задания.

### [Whisper](https://github.com/m-bain/whisperX) 

Это модель ASR, разработанная OpenAI, обученная на большом наборе данных разнообразного аудио. Несмотря на то, что он производит высокоточную транскрипцию, соответствующие временные метки находятся на уровне произнесения, а не на уровне каждого слова, и могут быть неточными на несколько секунд. OpenAI whisper изначально не поддерживает пакетную обработку.

### [Pyannote](https://github.com/pyannote/pyannote-audio)

Это инструментарий с открытым исходным кодом, написанный на Python для ведения дневника диктора. Основанный на платформе
машинного обучения Pitch, он поставляется с самыми современными предварительно обученными моделями и конвейерами, которые могут быть дополнительно точно настроены на ваши собственные данные для еще большей производительности.


## Преимущество нашего решения: 
Наше уникальное преимущество заключается в том, что мы предоставляем доступ к исходному коду нашего сервиса. Это дает возможность произвести более глубокую индивидуальную настройку сервиса в соответствии с уникальными потребностями и требованиями конкретной отрасли. Мы предлагаем не просто готовое решение, а инструмент, который можно адаптировать и оптимизировать для достижения максимальной эффективности.

## Используемые модели данных

В работе нашего сервиса есть возможность изменения модели с которой будет 
транскрибироваться текст. Существуют следующие модели:
|  Название  | Параметры | Англоязычная модель | Мультиязычная модель | Требуемая виртуальная оперативная память | Относительная скорость |
|:------:|:----------:|:------------------:|:------------------:|:-------------:|:--------------:|
|  tiny  |    39 M    |     `tiny.en`      |       `tiny`       |     ~1 GB     |      ~32x      |
|  base  |    74 M    |     `base.en`      |       `base`       |     ~1 GB     |      ~16x      |
| small  |   244 M    |     `small.en`     |      `small`       |     ~2 GB     |      ~6x       |
| medium |   769 M    |    `medium.en`     |      `medium`      |     ~5 GB     |      ~2x       |
| large  |   1550 M   |        N/A         |      `large`       |    ~10 GB     |       1x       |
## Работа с сервисом

#### Для работы с нашим сервисом вам достаточно всего лишь добавиться в наш tg-бот [Транскриптор](@transcriber_meet_bot) и следовать его инструкциям



## Бенчмарки

|  Название  | Скорость | 
|:------:|:----------:|
|  tiny  |    6 с/с    | 
|  base  |    5 с/с   | 
| small  |   2 с/с   | 
| medium |   1 с/с    |
| large  |   N/A   | 
 
 
# Описание

### Установка пакетов

#### 1. Установите необходимые репозиториев 
```python
 pip install -U openai-whisper
 pip install pyannote.audio
```
#### 2. Обновите пакеты если необходимо

```
pip install --upgrade --no-deps --force-reinstall git+https://github.com/openai/whisper.git
```

#### 3. Создайте токен доступа hf.co/settings/tokens.

#### 4. Получить токен для существующего бота. Это можно сделать в чате с ботом [BotFather](https://t.me/bote_father) с помощью команды /token

#### 5. Заимпортируйте необходимые библиотеки

```
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
```

#### 6. Создайте необходимые для работы сервиса классы
 они хранят в себе временныые метки и метки инициализации
```
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
```

#### 7. Создайте класс Service

```
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
```
 
_**Создайте ".env" файл в вашем python-проекте, и скопируйте туда содержимое файла "env-example"!!! Без него программа не будет работать**_

##### Один из примеров вывода
![Article](https://i.vas3k.club/75fa1ddfe8219a59992f17cd6e13effb0eff8328dd31ccf7c764e65e30eb04d2.jpg)

