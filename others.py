import os

def clear():
    os.system("cls")

def draw():
    print("-----------------------------------")

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