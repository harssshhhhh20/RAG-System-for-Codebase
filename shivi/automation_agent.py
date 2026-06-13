from shivi.desktop_tools import *

def handle_open_commands(command):
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

def process_automation(request):
      handle_open_commands(request)
    