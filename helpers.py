import os
import time
import sys

def clear():
    os.system("cls")

def draw():
    print("-" * 40)

def formatBuff(buff, stage, width = 6):
    if stage == 2:
        txt = f"{buff.upper()}↑↑"
    elif stage == 1:
        txt = f"{buff.upper()}↑"
    elif stage == 0:
        txt = f"{buff.upper()}"
    elif stage == -1:
        txt = f"{buff.upper()}↓"
    elif stage == -2:
        txt = f"{buff.upper()}↓↓"
    return txt.ljust(width)

def type_text(text, delay=0.1):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)