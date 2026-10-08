from shivi.desktop_tools import open_chrome, open_safari, open_url, open_vscode, open_whatsapp

# Checked in order; first keyword found in the request wins.
OPEN_ACTIONS = (
    (("vscode", "vs code", "visual studio code"), open_vscode),
    (("youtube",), lambda: open_url("https://youtube.com")),
    (("chrome",), open_chrome),
    (("safari",), open_safari),
    (("whatsapp",), open_whatsapp),
)


def handle_open_commands(command):
    command = command.lower()
    for keywords, action in OPEN_ACTIONS:
        if any(keyword in command for keyword in keywords):
            action()
            return True
    print("Unknown command")
    return False


def process_automation(request):
    handle_open_commands(request)
