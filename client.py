from tkinter.scrolledtext import *
from tkinter import *
from tkinter import Menu
from tkinter import colorchooser
import tkinter.messagebox
import socket
import threading
import sys
import os
import signal   # importing the used libraries


def send_connect_msg(username):
    msg = username + ',0'
    client_socket.send(msg.encode())  # Sending server the username to log in


def send_regular_msg(username, msg):
    message = username + ',1,' + msg
    client_socket.send(message.encode())  # Sending server simple regular text message


def add_admin(admin_name, user):
    message = admin_name + ',2,' + user
    client_socket.send(message.encode())  # Sending server a request to make someone admin


def kick_user(admin_name, username_to_kick):
    message = admin_name + ',3,' + username_to_kick
    client_socket.send(message.encode())   # Sending server a request to kick someone


def mute_user(admin_name, user_to_mute):
    message = admin_name + ',4,' + user_to_mute
    client_socket.send(message.encode())  # Sending server a request to mute someone


def view_managers(username):
    message = username + ',5'
    client_socket.send(message.encode())  # Sending the server a request to view the list of all the admins


def on_view_managers():
    view_managers(user_name)  # calling view_managers function


def unmute_user(admin_name, user_to_unmute):
    message = admin_name + ',6,' + user_to_unmute
    client_socket.send(message.encode())  # Sending server a request to unmute someone


def disconnect_client(username, msg):
    message = username + ',1,' + msg  # building disconnect message
    client_socket.send(message.encode())  # sending the server disconnect message
    client_socket.close()  # closing client socket
    sys.exit()  # exiting program


def on_exit():
    disconnect_client(user_name, 'quit')  # calling disconnect function


def check_input(username, msg):
    if msg.lower() == 'quit':
        disconnect_client(username, msg)  # disconnecting client if he wants to quit (sending disconnect message)
    elif msg.lower() == 'view-managers':
        view_managers(username)   # sending view managers request

    else:  # at other cases, messages may become more complicated
        try:
            words = msg.split(' ')  # we will split the string by words
            words[0] = words[0].lower()  # lower case the order (so that "QUIT" and others will work too (optional))
            if words[0] == 'inviteman':
                add_admin(username, words[1])  # (adding admin request) words[1] is the username we want to promote
            elif words[0] == 'shsh':
                mute_user(username, words[1])  # (mute user request) words[1] is the username we want to mute
            elif words[0] == 'getout':
                kick_user(username, words[1])  # (kick user request) words[1] is the username we want to kick
            elif words[0] + ' ' + words[1].lower() == 'no shsh':
                unmute_user(username, words[2])  # (unmute user request) words[2] is the username we want to unmute
            else:
                # we wil get here if the message he sent is nothing special (not an chat function)
                # + the message is more than one word (because words[0] didn't raised error) | *not important
                send_regular_msg(username, msg)  # sending the message to the server
        except IndexError:
            # if words[0] raise error, it means the message he sent is one word regular message
            send_regular_msg(username, msg)


def highlight_text(tag_name, lineno, start_char, end_char, fg_color=None):
    # selecting text
    chat_window.tag_add(tag_name, f'{lineno}.{start_char}', f'{lineno}.{end_char}')
    # changing the style of the selected text
    chat_window.tag_config(tag_name, foreground=fg_color)


def get_line():
    data = chat_window.get(1.0, "end-1c")
    return data.count('\n')
    # returning the number of lines are in the chat window


def send():
    # getting the content from message_window without spaces and breakdowns around the text
    content = message_window.get(1.0, "end-1c").strip()
    if len(content.encode('utf-8')) > 1024:
        tkinter.messagebox.showerror('Message Length Error',
                                     "Your message is too long.")
    elif content:
        check_input(user_name, content)
        chat_window.configure(state="normal")  # enable writing on chat window
        chat_window.insert(END, 'You: ' + content + '\n')  # output the message (like printing on chat window)
        highlight_text('you', get_line() - content.count('\n'), 0, 4, 'red')  # highlight 'You:' in red
        chat_window.configure(state="disable")  # disable writing on chat window
        chat_window.yview(END)  # automatic scroll down
        message_window.delete(1.0, END)  # clearing the message window


def cancel():
    client_socket.close()  # closing client socket
    sys.exit()  # exiting program


def login():
    global user_name
    name = entry.get().strip()
    if check(name):  # if username is valid
        try:
            send_connect_msg(name)  # sending server the connect message
            received_data = client_socket.recv(1024).decode()  # receiving information from the server
        except WindowsError:
            # if it fails, we will print error message and exit | sever stopped running while client on login window
            tkinter.messagebox.showerror('Server Error',
                                         f"Our Chat Room Just Closed. Please Try Again Later!")
            sys.exit()
        if received_data == 'TAKEN':  # checking if the username is available
            error.config(text=name + ' is already taken.')
        else:
            user_name = name
            login_root.destroy()  # username is valid and available - closing login window


def check(username):
    if username == '':
        error.config(text="You Must Enter Username!")  # showing error message
        return False
    elif ' ' in username:
        error.config(text="You Cannot Use Spaces!")  # showing error message
        return False
    elif username[0] == '@':
        error.config(text="You Cannot Start Your Name With '@'!")  # showing error message
        return False
    else:
        return True


def login_gui():
    global login_root
    login_root = Tk()
    login_root.title('login')
    login_root.geometry('500x270+350+150')
    login_root.resizable(height=False, width=False)
    login_root.configure(background='#15191f')

    # building title
    login_title = Label(login_root, text='Log In', bg='#15191f', font=('Segoe UI', 24, 'bold'), fg='white')
    login_title.pack(side='top')

    # requesting for text
    text = Label(login_root, text='Please Enter Your Username To Login',
                 bg='#15191f', fg='white', font=('Segoe UI', 16))
    text.place(x=70, y=60)

    # saving place for error message
    global error
    error = Label(login_root, text='', bg='#15191f', font=('Segoe UI', 14, 'bold'), fg='red')
    error.place(x=70, y=90)

    # building 'Username:' text before entry
    username = Label(login_root, text='Username:', bg='#15191f', font=('Segoe UI', 14), fg='white')
    username.place(x=100, y=130)

    # building entry (the place where the user will enter his username)
    global entry
    entry = Entry(login_root, bg='white', fg='black', font=('Segoe UI', 14), bd=5)
    entry.place(x=200, y=130, width=200, height=35)

    # building submit button
    login_button = Button(login_root, text='Login', bg='#21b043', activebackground='#40e668', width=12, height=5,
                          font=('Segoe UI', 14), fg='white', command=login, bd=5)
    login_button.place(x=150, y=200, height=50, width=70)

    # building cancel button
    cancel_button = Button(login_root, text='Cancel', bg='#ff0011', activebackground='#ff2e3c', width=12, height=5,
                           font=('Segoe UI', 14), fg='white', command=cancel, bd=5)
    cancel_button.place(x=300, y=200, height=50, width=70)

    login_root.mainloop()


def receive():
    while True:
        try:
            received_data = client_socket.recv(1024).decode()  # receiving information from the server
            # received_data == "You Got Kicked From The Chat!" or
            if received_data == "":  # if he user got kicked
                tkinter.messagebox.showinfo('Kick',
                                            "You Got Kicked Out From The Chat! Come back later..")
                os.kill(os.getpid(), signal.SIGTERM)  # kill and exiting program
            chat_window.configure(state="normal")  # enable writing on chat window
            chat_window.insert(END, received_data + '\n')  # output the message (like printing on chat window)
            try:
                # checking if the received data came from my server (with time like that "18:00:33 | ")
                if received_data[2] == ':' and received_data[5] == ':' and received_data[9] == '|':
                    # if it does, we will highlight the time in green
                    highlight_text('time', get_line() - received_data.count('\n'), 0, 10, 'green')
            except IndexError:
                # in case the received data is too short, the message is not from my server
                # (with time like that "18:00:33 | ") so we won't highlight the time in green, just pass
                pass
            chat_window.configure(state="disable")  # disable writing on chat window
            chat_window.yview(END)  # automatic scroll down
        except ConnectionAbortedError:  # client closed the window | *console edition
            break
        except ConnectionResetError:  # server closed
            tkinter.messagebox.showerror('Server Error',
                                         "Our Chat Room Just Closed. Come Back Later!")
            os.kill(os.getpid(), signal.SIGTERM)  # kill and exiting program


def start_gui():
    global login_root, root, title, chat_window, message_window, send_button
    root = Tk()
    title = Label(root)
    chat_window = ScrolledText(root)
    message_window = ScrolledText(root)
    send_button = Button(root)
    try:
        root.title('Chat Room - ' + user_name)
    except NameError:  # client closed the login root so username is not defined
        cancel()
    root.geometry('950x550+60+60')
    root.resizable(height=False, width=False)
    root.configure(background='white')
    title.config(text='Chat Room - ' + user_name, bg='white', font=('Segoe UI', 24, 'bold'), cursor='arrow')
    title.pack(side='top')

    # building chat window
    chat_window.config(bg='#15191f', width=50, height=8, fg='white',
                       font=('Segoe UI', 14), bd=7, cursor='arrow')
    chat_window.place(x=5, y=60, width=940, height=420)
    chat_window.configure(state="disabled")

    # building message window
    message_window.config(bg='#15191f', width=30, height=4, fg='white', font=('Segoe UI', 14), bd=5)
    message_window.place(x=5, y=490, width=850, height=50)

    # building send button
    send_button.config(text='SEND', bg='#21b043', activebackground='#40e668', width=12, height=5,
                       font=('Segoe UI', 14), fg='white', command=send, bd=5)
    send_button.place(x=865, y=490, height=50, width=70)


def connect():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # creating client socket
    # getting username to login! client will join chat only after he log in
    try:
        # connecting to the server
        client_socket.connect(('127.0.0.1', 2000))
    except (ConnectionRefusedError, TimeoutError) as e:  # e is the error
        # if it fails, we will print error message and exit | sever not running
        tkinter.messagebox.showerror('Server Error',
                                     f"Our Chat Room Is Close Now. Please Try Again Later\n{e}")
        sys.exit()  # exiting program


def on_clear_chat():
    chat_window.configure(state="normal")  # enable writing on chat window
    chat_window.delete(1.0, END)  # clearing the chat window
    chat_window.configure(state="disable")  # disable writing on chat window


def on_text_color():
    color = colorchooser.askcolor()[1]  # getting the color (HEX | #XXXXXX)
    chat_window.config(fg=color)  # changing chat window text color
    message_window.config(fg=color)  # changing message window text color


def on_background_color():
    color = colorchooser.askcolor()[1]  # getting the color (HEX | #XXXXXX)
    chat_window.config(bg=color)  # changing chat window background color
    message_window.config(bg=color)  # changing message window background color


def on_window_color():
    color = colorchooser.askcolor()[1]  # getting the color (HEX | #XXXXXX)
    root.config(bg=color)  # changing window background color
    title.config(bg=color)  # changing title background color


def paint(text):  # paint function especially for 'help' menu bar button
    lines = text.split('\n')
    line_index = 6  # number of lines in help_msg (*on_help)
    total_lines = get_line()  # total lines are in chat window
    for line in lines:  # for every line from top to bottom
        # highlight order in light blue | total_lines-line_index is the line number in relation to all chat lines
        highlight_text('order', total_lines-line_index, 0, line.find('|')+1, "#728df7")
        # highlight the needed message to write in green | rfind finds the index of the last show of the char (' ')
        highlight_text('msg', total_lines-line_index, line.find('|')+1, line.rfind(' ') + 1, "#8aff4f")
        line_index -= 1


def on_help():
    help_msg = "Private Message | !<receiver_name> <message> \n" \
               "Add Admin | inviteMan <username_to_promote> \n" \
               "Mute User | shsh <username_to_mute> \n" \
               "UnMute user | no shsh <username_to_unmute> \n" \
               "Kick user | getout <username_to_kick> \n" \
               "View Admins | view-managers \n" \
               "Quit Chat | quit \n"
    chat_window.configure(state="normal")  # enable writing on chat window
    chat_window.insert(END, help_msg)  # output the message (like printing on chat window)
    paint(help_msg)
    chat_window.configure(state="disable")  # disable writing on chat window
    chat_window.yview(END)  # automatic scroll down


def set_menu():
    menu_bar = Menu(root)  # creating bar menu
    root.config(menu=menu_bar)  # linking bar menu to root
    menu_bar.add_command(label="Exit", command=on_exit)  # add exit command
    menu_bar.add_command(label="Help", command=on_help)  # add help command
    menu_bar.add_command(label="View Managers", command=on_view_managers)  # add view managers command
    menu_bar.add_command(label="Clear Chat", command=on_clear_chat)  # add clear chat command
    colors_menu = Menu(menu_bar)
    colors_menu.add_command(label="Text Color", command=on_text_color)  # add change text color command
    colors_menu.add_command(label="Background Color", command=on_background_color)  # add change background command
    colors_menu.add_command(label="Window Color", command=on_window_color)  # add change window color command
    menu_bar.add_cascade(label="Colors", menu=colors_menu)  # adding the menu


if __name__ == '__main__':
    global login_root, client_socket, entry, error, user_name, root, title, chat_window, message_window, send_button
    connect()  # create socket connection
    login_gui()  # getting username to login
    start_gui()  # starting main gui (the actual chat)
    set_menu()  # building menu
    receive_t = threading.Thread(target=receive)
    receive_t.start()  # starting the receive thread
    root.mainloop()
    # we will get here if client closed the gui window, so we disconnect him
    disconnect_client(user_name, 'quit')
