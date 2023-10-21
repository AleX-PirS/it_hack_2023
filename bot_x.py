import telebot
import regex
from threading import Thread
import whisperx
import gc
from pytube import YouTube
import time
import os
from dotenv import load_dotenv

load_dotenv()

try:
    hugging_face_token = os.getenv("HUGGING_FACE_TOKEN")
    if hugging_face_token is None: raise
    tg_bot_token = os.getenv("TG_BOT_TOKEN")
    if tg_bot_token is None: raise
except:
    print("invalid .env data")
    # logging("invalid .env data")
    os._exit(0)

youtybe_reg = "https:\/\/www\.youtube\.com\/watch\?v="
youtybe_location = "/temp/"

max_length=4000

ml_model = "small"

device = "cpu"

bot = telebot.TeleBot(tg_bot_token)

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

    model = whisperx.load_model("large-v2", device, compute_type="float16")
    result = model.transcribe(fn, batch_size=16)
    print(result["segments"])

    # 2. Align whisper output
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, fn, device, return_char_alignments=False)
    print(result["segments"])

    # 3. Assign speaker labels
    diarize_model = whisperx.DiarizationPipeline(use_auth_token=hugging_face_token, device=device)

    # add min/max number of speakers if known
    diarize_segments = diarize_model(fn)
    # diarize_model(audio, min_speakers=min_speakers, max_speakers=max_speakers)

    result = whisperx.assign_word_speakers(diarize_segments, result)
    print(diarize_segments)
    print(result["segments"]) # segments are now assigned speaker IDs
    return
    # awpdjoaiwjdoiajwodijawidjoawijdoaiwjdoiajwdiajwodjawosejfospqkwpoiapwkdpawd[akwdpok]

    # model = whisper.load_model(ml_model)
    # res = model.transcribe(fn)

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
    