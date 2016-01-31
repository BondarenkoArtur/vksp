import vk
import os, sys
from colorama import Fore, Style, init
from time import  sleep


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

init() # start colorama

term_size = 80 # width terminal windows

if sys.platform == 'win32': # cause smiles brings exceptions
    os.system('chcp 65001')

# Templates for messages
MESSAGE_AUTHOR = "{cyan}{first_name} {last_name}{reset} == {green}(https://vk.com/id{bold}{red}{id}{reset}{green}){reset} == "
FWD_MESSAGE_AUTHOR = "Repost {yellow}{first_name} {last_name}{reset} == {green}(https://vk.com/id{bold}{red}{id}{reset}{green}){reset}"

# INSERT YOUR TOKEN https://oauth.vk.com/authorize?client_id=4171638&scope=343487&redirect_uri=https://oauth.vk.com/blank.html&response_type=token
session = vk.Session(access_token='INSERT_YOUR_TOKEN')
api = vk.API(session, v='5.44', lang='ru')

def format(str, *args, **kw): # own bycicles
    buf = kw.copy() if kw else {}
    buf.update(formating)
    return str.format(*args, **buf)

def printMessages(messages, outfile=sys.stdout):
    for mes in messages:
        if "from_id" in mes:
            user = api.users.get(user_ids=mes['from_id'])[0]
        else:
            user = api.users.get(user_ids=mes['user_id'])[0]
        print(format(MESSAGE_AUTHOR, **user), end='', file=outfile)
        print(mes_statuses[mes['read_state']], file=outfile)
        print(mes['body'], file=outfile)
        if 'fwd_messages' in mes: # checking forwarded messages and attachment them
            for fwd_mes in mes['fwd_messages']:
                fwd_user = api.users.get(user_ids=fwd_mes['user_id'])[0]
                print(format(FWD_MESSAGE_AUTHOR, **fwd_user), file=outfile)
                print(">>> {body}".format(**fwd_mes), file=outfile)
                sleep(0.25)
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

        print(format("{bold}{0}{reset}", "="*term_size))
        sleep(0.25)

def showUnreadDialogs(**kw):
	dialogs = api.messages.getDialogs(unread='1')
	printMessages([i['message'] for i in dialogs['items']])

def showDialogs(**kw):
    dialogs = api.messages.getDialogs(**kw)
    printMessages([i['message'] for i in dialogs['items']])

def showDialog(**kw):
    if 'user_id' in kw:
        messages = api.messages.getHistory(**kw)
        printMessages(messages['items'][::-1]) # print reverted list (new below)

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

showDialog(user_id='30815965', count=5)

if __name__ == "__main__":
    while 1:
        try:
            print(exec(input(">>> ")))
        except Exception as e:
            print(e)
            continue
