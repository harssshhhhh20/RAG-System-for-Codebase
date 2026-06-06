from faster_whisper import WhisperModel

model = WhisperModel(
    "base",
    compute_type="int8"
)
audio_file = "command.wav"
def transcribe_audio():
    segments, info = model.transcribe(
    audio_file
)
    text = ""
    for segment in segments:
        text+=segment.text
    return text.strip()
