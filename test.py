from voice_agent import transcribe_stream

for text in transcribe_stream():

    print(
        f"TEXT: {text}"
    )