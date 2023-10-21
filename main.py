import whisper
from pytube import YouTube
yt = YouTube("https://www.youtube.com/watch?v=cqu3uKuW_bg")
fn = yt.streams.filter(type="audio")[0].download()

model = whisper.load_model("small")
res = model.transcribe(fn)

print(res["text"])