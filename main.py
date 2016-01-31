import threading
from time import gmtime, strftime
import os
import sys
import time

import vk
from colorama import Fore, Style, init
import speech_recognition as sr
import google_speech as gs

formating = {"green": Fore.GREEN,
             "red": Fore.RED,
             "white": Fore.WHITE,
             "blue": Fore.BLUE,
             "cyan": Fore.CYAN,
             "yellow": Fore.YELLOW,
             "bold": Style.BRIGHT,
             "reset": Style.RESET_ALL}

mes_statuses = {1: "{bold}{blue}red{reset} ==".format(**formating),
                0: "{bold}{red}unread{reset} ==".format(**formating)}

init()  # start colorama

term_size = 80  # width terminal windows

if sys.platform == 'win32':  # cause smiles brings exceptions
    os.system('chcp 65001')

# Templates for messages
MESSAGE_AUTHOR = "{cyan}{first_name} {last_name}{reset} == {green}(https://vk.com/id{bold}{red}{id}{reset}{green}){reset} == "
FWD_MESSAGE_AUTHOR = "Repost {yellow}{first_name} {last_name}{reset} == {green}(https://vk.com/id{bold}{red}{id}{reset}{green}){reset}"

# INSERT YOUR TOKEN https://oauth.vk.com/authorize?client_id=4171638&scope=343487&redirect_uri=https://oauth.vk.com/blank.html&response_type=token
session = vk.Session(access_token='')
api = vk.API(session, v='5.44', lang='ru')


def format(str, *args, **kw):  # own bycicles
    buf = kw.copy() if kw else {}
    buf.update(formating)
    return str.format(*args, **buf)

def say(str):
    gs.main(str, lang='ru', sox_effects='')

def printMessages(messages, outfile=sys.stdout):
    for mes in messages:
        if "from_id" in mes:
            user = api.users.get(user_ids=mes['from_id'])[0]
        else:
            user = api.users.get(user_ids=mes['user_id'])[0]
        print(format(MESSAGE_AUTHOR, **user), end='', file=outfile)
        say(format(MESSAGE_AUTHOR, **user))
        print(mes_statuses[mes['read_state']], file=outfile)
        say(mes_statuses[mes['read_state']])
        print(mes['body'], file=outfile)
        say(mes['body'])
        if 'fwd_messages' in mes:  # checking forwarded messages and attachment them
            for fwd_mes in mes['fwd_messages']:
                fwd_user = api.users.get(user_ids=fwd_mes['user_id'])[0]
                print(format(FWD_MESSAGE_AUTHOR, **fwd_user), file=outfile)
                say(format(FWD_MESSAGE_AUTHOR, **fwd_user))
                print(">>> {body}".format(**fwd_mes), file=outfile)
                say(">>> {body}".format(**fwd_mes))
                time.sleep(0.25)
        if 'attachments' in mes:
            print(format("{yellow}{bold}Attachments:{reset}"), file=outfile)
            attachments = ''
            for attach in mes['attachments']:
                if 'wall' in attach:
                    wall = attach['wall']
                    if 'text' in wall:
                        print("{text}".format(**wall), file=outfile)
                    if 'attachments' in wall:
                        print(format("{yellow}{bold}Repost has attachments:{reset}"), file=outfile)
                        elements = ''
                        for include in wall['attachments']:
                            elements += "{type}".format(**include) + ' '
                        print(elements)
                else:
                    attachments += "{type}".format(**attach) + ' '
            print(attachments)

        print(format("{bold}{0}{reset}", "=" * term_size))
        time.sleep(0.25)


def showUnreadDialogs(**kw):
    dialogs = api.messages.getDialogs(unread='1')
    printMessages([i['message'] for i in dialogs['items']])


def showDialogs(**kw):
    dialogs = api.messages.getDialogs(**kw)
    printMessages([i['message'] for i in dialogs['items']])


def showDialog(**kw):
    if 'user_id' in kw:
        messages = api.messages.getHistory(**kw)
        printMessages(messages['items'][::-1])  # print reverted list (new below)


def showFriends(only_online=False, **kw):
    if not "fields" in kw:
        kw['fields'] = 'online'
    else:
        kw['fields'] += ", online"
    if not "order" in kw:
        kw['order'] = 'hints'
    frs = api.friends.get(**kw)['items']
    if only_online:
        frs = list(filter(lambda x: x['online'], frs))
    max_no_symbs = len(str(len(frs)))

    for i, fr in enumerate(frs):
        if fr['online']:
            print(format("{green}[{0}][✔]", str(i+1).zfill(max_no_symbs)), end=" ")
        else:
            print(format("[{0}][✖]", str(i+1).zfill(max_no_symbs)), end=" ")
        print("{first_name} {last_name} (https://vk.com/id{id})".format(**fr), end="")
        print(format("{reset}"))


def sendMessage(**kw):
    if 'user_id' in kw:
        user = api.users.get(user_ids=kw['user_id'], name_case='dat')[0]
        print("Send message to {first_name} {last_name}".format(**user))
    else:
        user_id = input("User ID: ")
        sendMessage(user_id=user_id)
        return
    if 'message' not in kw:
        message = input("Type msg: ")
        api.messages.send(message=message, **kw)
    else:
        api.messages.send(**kw)

    if 'user_id' in kw:
        yn = input("Open dialog with user? [y,т/n,н][n]: ")
        if 'yes' in yn.lower() or 'y' in yn.lower() or 'т' in yn.lower() or 'так' in yn.lower():
            showDialog(count=10, user_id=kw['user_id'])


def currentTime():
    time = strftime("%H:%M", gmtime())
    say(time)
    pass


def compareToCommands(value):
    if value.find("message") != -1:
        showUnreadDialogs()
        pass
    if value.find("time") != -1:
        currentTime()
        pass

r = sr.Recognizer()
m = sr.Microphone()

try:
    print("A moment of silence, please...")
    with m as source:
        r.adjust_for_ambient_noise(source)
        print("Set minimum energy threshold to {}".format(r.energy_threshold))
        while True:
            print("Say something!")
            audio = r.listen(source)
            print("Got it! Now to recognize it...")
            try:
                # recognize speech using Google Speech Recognition
                value = r.recognize_google(audio)
                compareToCommands(value)
                # we need some special handling here to correctly print unicode characters to standard output
                if str is bytes: # this version of Python uses bytes for strings (Python 2)
                    print(u"You said {}".format(value).encode("utf-8"))
                else: # this version of Python uses unicode for strings (Python 3+)
                    print("You said {}".format(value))
            except sr.UnknownValueError:
                print("Oops! Didn't catch that")
            except sr.RequestError as e:
                print("Uh oh! Couldn't request results from Google Speech Recognition service; {0}".format(e))
except KeyboardInterrupt:
    pass