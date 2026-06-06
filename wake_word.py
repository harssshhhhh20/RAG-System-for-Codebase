from shivi import route_requests, classify_request
from record_audio import record_audio
from voice_agent import transcribe_audio

WAKE_WORDS = [
    "wake up",
    "boot up",
    "hello"
]

SLEEP_WORDS = [
    "goodbye",
    "exit",
    "sleep",
    "go to sleep"
]

def is_wake_word(text):
    text = text.lower().strip()
    return any(
        wake_word in text
        for wake_word in WAKE_WORDS
    )

def is_sleep_word(text):
    text = text.lower().strip()
    return any(
        sleep_word in text
        for sleep_word in SLEEP_WORDS
    )

def main():
    print("Agent SHIVI started")
    while True:
        print("Listening for wake word")
        record_audio()
        text = transcribe_audio()
        print(f"Heard: {text}")
        if not text:
            continue
        if is_wake_word(text):
            print("Agent activated")
            while True:
                print("Listening for command")
                record_audio()
                command = transcribe_audio()
                print(f"Command: {command}")
                if not command:
                    continue
                if is_sleep_word(command):
                    print("Agent sleeping")
                    break
                intent = classify_request(
                    command
                )
                print(
                    f"Detected Intent: {intent}"
                )
                route_requests(
                    command,
                    intent
                )
        else:
            print("Wake word not detected")

if __name__ == "__main__":
    main()