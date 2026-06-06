from desktop_tools import *
from langchain_ollama import ChatOllama
from voice_agent import *
from record_audio import *

llm = ChatOllama(
      model="qwen3:4b",
      temperature=0
)

def intent_routing(command):
      prompt = f"""
        Return ONLY one of:
        vscode
        chrome
        youtube
        safari
        whatsapp
        netmirror
        unknown

        Examples:

        open vscode
        vscode

        launch visual studio code
        vscode

        open youtube
        youtube

        open whatsapp
        whatsapp

        Command:
        {command}
        """
      response = llm.invoke(prompt)
      return response.content.strip().lower()


def handle_open_commands(request):
    command = intent_routing(request)
    print(f"Intent: {command}")
    if "vscode" in command:
        open_vscode()
        return
    elif "chrome" in command:
        open_chrome()
        return
    elif "youtube" in command:
            open_url("https://youtube.com")
            return
    elif "safari" in command:
            open_safari()
            return
    elif "whatsapp" in command:
            open_whatsapp()
            return
    elif "netmirror" in command:
            open_chrome("netmirror")
            return
    else:
        print("Unknown command")

def main():
      record_audio()
      command = transcribe_audio()
      print(command)
      handle_open_commands(command)

if __name__ == "__main__":
      main()
    