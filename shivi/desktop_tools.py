import os, subprocess

def open_vscode():
    subprocess.Popen(
        ["open","-a","Visual Studio Code"]
    )

def open_chrome():
    subprocess.Popen(
        ["open","-a","Google Chrome"]
    )

def open_safari():
    subprocess.Popen(
        ["open","-a","Safari"]
    )

def open_whatsapp():
    subprocess.Popen(
        ["open","-a","WhatsApp"]
    )

def open_folder(folder_path):
    subprocess.Popen(
        ["open",folder_path]
    )

def open_url(url):
    subprocess.Popen(
        ["open",url]
    )