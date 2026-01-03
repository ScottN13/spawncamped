import threading
import time
import subprocess

async def stopBot():
    bot_thread

if __name__ == "__main__":
    # webpanel_process = subprocess.Popen(["uvicorn", "webpanel:app", "--host", "0.0.0.0", "--port", "8000"])

    bot_thread = threading.Thread(target=subprocess.run, args=(["python", "main.py"],))
    webpanel_thread = threading.Thread(target=subprocess.run, args=(["python", "webpanel.py"],))

    bot_thread.start()
    webpanel_thread.start()

# This script starts both the bot and the web panel in separate threads.