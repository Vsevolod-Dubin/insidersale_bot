# serve_and_run_bot.py
import subprocess
import threading
import time
import sys


def run_django():
    subprocess.call([sys.executable, "manage.py", "runserver", "0.0.0.0:8000"])


def run_bot():
    time.sleep(5)  # подождать, пока Django поднимется
    subprocess.call([sys.executable, "-m", "bot.bot_main"])


t1 = threading.Thread(target=run_django)
t2 = threading.Thread(target=run_bot)

t1.start()
t2.start()

t1.join()
t2.join()
