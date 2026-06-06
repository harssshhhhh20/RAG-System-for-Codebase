import sounddevice as sd
from scipy.io.wavfile import write

duration = 5
sample_rate = 16000

def record_audio():
    print("Speak Now...")

    audio = sd.rec(
        int(duration*sample_rate),
        samplerate=sample_rate,
        channels=1
    )
    sd.wait()
    write("command.wav",sample_rate,audio)
    print("saved")