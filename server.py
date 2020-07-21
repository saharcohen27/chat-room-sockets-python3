import socket  # importing the used libraries
import select
from datetime import datetime


def broadcast():
    # calculate current time
    time = datetime.now().strftime("%H:%M:%S") + " | "
    for message in messages:  # sending all messages that have been sent
        (client_sock, msg) = message
        if client_sock in wlist:
            print(time + msg)  # printing on server
            for user, sock in valid_users.items():
                # sending the message to everyone except the server and the sender
                # + only if the receiver is logged in
                if sock is not client_sock and sock is not server_socket:
                    # sending the message
                    sock.send((time + msg).encode())
        messages.remove(message)  # after the message have been sent, we will remove it so it won't resend


def check_all(msg, client):
    if msg:
        lst = msg.split(',', 2)  # maximum 2 splits
        num_order = ord(lst[1]) - ord('0')  # converting the num order from string to int
        username = lst[0]  # the name of the user who sent the message
        if num_order == 0:  # checking if the message is login request
            connect(client, username)
        elif num_order == 1 and lst[2]:  # if the user wants to send message, and there is a message
            if lst[2].lower() == 'quit':  # checking if the message is quit request
                disconnect(client, username)
            elif lst[2][0] == '!' and lst[2].count(' ') != 0:  # checking if the message is private message
                send_private_msg(client, username, lst[2][1:lst[2].index(' ')], lst[2][lst[2].index(' ') + 1::])
                # lst[2][1:lst[2].index(' ')] is the user who will receive the message (RECEIVER)
                # lst[2][lst[2].index(' ') + 1::] is the message
            else:
                send_message(client, username, lst[2])  # if we got here, the message is regular message
        elif num_order == 2:  # checking if the message is an 'Add Admin' request
            add_admin(client, username, lst[2])
        elif num_order == 3:  # checking if the message is kick request
            kick_user(client, username, lst[2])
        elif num_order == 4:  # checking if the message is mute user request
            mute_user(client, username, lst[2])
        elif num_order == 5:  # checking if the message is view managers request
            view_managers(client, username)
        elif num_order == 6:  # checking if the message is unmute user request
            unmute_user(client, username, lst[2])


def send_private_msg(client, sender, receiver, message):
    time = datetime.now().strftime("%H:%M:%S") + " | "  # calculate current time
    if sender not in muted_users:
        if sender in admins:
            msg = time + '!@' + sender + ': ' + message  # sending the message as an 'Admin' format (with '@')
        else:
            msg = time + '!' + sender + ': ' + message  # sending the message as an 'Regular' format (without '@')
        try:
            valid_users[receiver].send(msg.encode())  # trying to send the message
            print(time + "!" + sender + ' (to: ' + receiver + '): ' + message)  # printing on server
        except KeyError:
            # if 'valid_users[receiver]' raised error, the user wasn't found
            if receiver in admins:
                error_msg = "* Admin @" + receiver + " Not Online *"
            else:
                error_msg = "* User " + receiver + " Not Online *"
            client.send((time + error_msg).encode())  # sending the sender Error message
    else:
        if receiver not in admins:  # if user is muted and receiver is not an admin
            msg = time + "* You Cannot Speak Here *"
            client.send(msg.encode())  # the message he sent wont be broadcast and he will get error message
        else:
            # if user is muted and receiver is an admin
            msg = time + '!' + sender + ': ' + message
            try:
                valid_users[receiver].send(msg.encode())  # trying to send the message
                print(time + "!" + sender + ' (to: ' + receiver + '): ' + message)  # printing on server
            except KeyError:
                # if 'valid_users[receiver]' raised error, the Admin wasn't found
                error_msg = "* Admin @" + receiver + " Not Online *"
                client.send((time + error_msg).encode())  # sending the sender Error message


def mute_user(client, admin, user):
    time = datetime.now().strftime("%H:%M:%S") + " | "  # calculate current time
    if admin in admins and user not in admins:  # only admin can use that command and he cannot do it at another admin
        if user in muted_users:  # checking if the user is already muted
            error_msg = time + "* User " + user + " Is Already Muted! *"
            client.send(error_msg.encode())  # sending the sender error message
        else:
            # in case we want to open this option only if the user is online, uncomment these lines
            # try:
            # if valid_users[user]:
            # if user is online, we will send everyone he got muted

            # sending everyone that user muted
            messages.append((client, "* " + user + " muted by @" + admin + " *"))
            msg = time + "* You Successfully Muted " + user + " *"
            client.send(msg.encode())  # sending the admin success message
            muted_users.append(user)  # adding user to the muted users list

            # in case we want to open this option only if the user is online, uncomment these lines
            # except KeyError:
            #     # if 'valid_users[receiver]' raised error, the Admin wasn't found
            #     error_msg = time + "* User " + user + " Not Found *"
            #     client.send(error_msg.encode())  # sending the sender Error message
    else:
        # if sender is not an admin he cannot use that command
        # or if he is an admin but he tries to mute another admin
        msg = time + "* You have no permission to do it! *"
        client.send(msg.encode())  # sending the sender Error message


def unmute_user(client, admin, user):
    time = datetime.now().strftime("%H:%M:%S") + " | "  # calculate current time
    if admin in admins:  # only admin can unmute admin
        if user not in muted_users:  # checking if the user is already muted
            error_msg = time + "* User " + user + " Is Not Muted! *"
            client.send(error_msg.encode())  # sending the admin error message
        else:
            # sending everyone that user unmuted
            messages.append((client, "* " + user + " Unmuted by @" + admin + " *"))
            msg = time + "* You Successfully UnMuted " + user + " *"
            client.send(msg.encode())  # sending the admin success message
            muted_users.remove(user)  # removing user from muted_users list (basically unmute him)
    else:
        msg = time + "* You have no permission to do it! *"
        client.send(msg.encode())  # sending him error message


def view_managers(client, username):
    msg = "* List of admins:\n"
    index = 1  # numbering the admins
    for admin in admins:
        msg += str(index) + ') ' + admin  # <index>) <admin-username>
        if admin in valid_users:
            msg += " - Online"  # showing if admin is online
        else:
            msg += " - Offline"  # showing if admin is offline
        msg += '\n'  # breakdown
        index += 1

    time = datetime.now().strftime("%H:%M:%S") + " | "  # calculate current time
    if username in admins:
        print(time + '* @' + username + ' Asked To View Managers:')  # printing on server
    else:
        print(time + '* ' + username + ' Asked To View Managers:')  # printing on server
    print(msg[2::])  # printing on server the admins list without the '* '
    client.send((time + msg).encode())  # sending the admins list to the client who asked it


def add_admin(client, admin, user):
    time = datetime.now().strftime("%H:%M:%S") + " | "  # calculate current time
    if admin in admins:  # only admin can make others admins
        if user in admins:  # if the user is already an admin
            error_msg = time + "* User " + user + " Is Already An Admin *"
            client.send(error_msg.encode())  # sending the sender (admin) error message
        else:
            # in case we want to open this option only if the user is online, uncomment these lines
            # try:
            # if valid_users[user]:  # if the user is online

            # sending everyone that user got promoted
            messages.append((client, "* " + user + " Just Became An Admin! by @" + admin + " *"))
            msg = time + "* You Successfully Promoted " + user + " *"
            client.send(msg.encode())  # sending the admin that his request successfully made
            admins.append(user)  # adding him to the admins list

            if user in muted_users:
                # if the user we promoted is muted, we will unmute him
                muted_users.remove(user)

            # in case we want to open this option only if the user is online, uncomment these lines
            # except KeyError:
            #     # if 'valid_users[receiver]' raised error, the Admin wasn't found
            #     error_msg = time + "* User " + user + " Not Found *"
            #     client.send(error_msg.encode())  # sending error message
    else:
        msg = time + "* You Have No Permission To Do It! *"
        client.send(msg.encode())


def send_message(client, username, msg):
    time = datetime.now().strftime("%H:%M:%S") + " | "  # calculate current time
    if username not in muted_users:
        # the sender not muted, so we check:
        if username in admins:  # if he is an admin
            # sending the message as an 'Admin' format (with '@')
            messages.append((client, '@' + username + ": " + msg))  # sending message
        else:  # he is not an admin
            # sending the message as an 'Regular' format (without '@')
            messages.append((client, username + ": " + msg))  # sending message
    else:
        # the sender is muted
        msg = time + "* You Cannot Speak Here *"
        client.send(msg.encode())  # sending him error message


def disconnect(client, username):
    if username in admins:
        # sending the message as an 'Admin' format (with '@')
        messages.append((client, "* @" + username + " Has Left The Chat *"))
    else:
        # sending the message as an 'Regular' format (without '@')
        messages.append((client, "* " + username + " Has Left The Chat *"))
    print('Connection With Client Closed [requested quit]')
    open_client_sockets.remove(client)  # removing from the list
    del valid_users[username]  # deleting user from the dictionary


def kick_user(client, admin, user_to_kick):
    time = datetime.now().strftime("%H:%M:%S") + " | "  # calculate current time
    if admin in admins and user_to_kick not in admins:
        try:  # assuming the requested client to kick is in chat
            # sending the kicked user that he got kicked *optional
            # valid_users[user_to_kick].send("You Got Kicked From The Chat!".encode())

            valid_users[user_to_kick].close()
            open_client_sockets.remove(valid_users[user_to_kick])  # removing from the list
            del valid_users[user_to_kick]  # deleting user from the dictionary

            # sending everyone that user_to_kick got kicked
            messages.append((client, "* " + user_to_kick + " Was Kicked From The Chat By @" + admin + " *"))

            msg = time + "* You Successfully Kicked " + user_to_kick + " *"
            client.send(msg.encode())  # sending the admin that kicked the user, that his request fulfilled
            print('Connection With Client Closed [client was kicked]')

        except KeyError:  # if the program raises error so user wasn't found
            error_msg = time + "* User " + user_to_kick + " Not Found *"
            client.send(error_msg.encode())  # sending error message
    else:
        # sender not in admins or he is, but he wants to kick another admin
        msg = time + "* You have no permission to do it! *"
        client.send(msg.encode())  # send error message


def connect(client, username):
    if username in valid_users:
        # if username is already connected to chat
        client.send("TAKEN".encode())  # 'TAKEN' means the username is already taken
    else:
        client.send("ACCEPT".encode())  # 'ACCEPT' means the username is available

        if username in admins:
            # sending the message as an 'Admin' format (with '@')
            messages.append((client, "* The Admin @" + username + " Was Connected *"))
        else:
            # sending the message as an 'Regular' format (without '@')
            messages.append((client, "* The User " + username + " Was Connected *"))

        valid_users.update({username: client})  # adding to dictionary


if __name__ == '__main__':
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # the listening socket

    try:
        server_socket.bind(('0.0.0.0', 2000))
    except WindowsError:
        # sometimes windows have problems with '0.0.0.0' so we will use '127.0.0.1' instead
        server_socket.bind(('127.0.0.1', 2000))

    server_socket.listen(5)  # listening to up to 5 users
    open_client_sockets = [server_socket]

    admins = ['admin']  # at the beginning, we have one admin called 'admin'
    muted_users = []  # at the beginning, we don't have any muted users
    valid_users = {}  # at the beginning, we don't have online users
    messages = []  # at the beginning, we don't any messages

    current_time = datetime.now().strftime("%H:%M:%S") + " | "  # calculate current time
    print(current_time + "Chat Is Open!")
    while True:
        rlist, wlist, xlist = select.select(open_client_sockets, open_client_sockets, open_client_sockets)
        for client_socket in rlist:
            if client_socket is server_socket:
                connection, address = server_socket.accept()
                open_client_sockets.append(connection)
                current_time = datetime.now().strftime("%H:%M:%S") + " | "  # calculate current time
                print(current_time + "New Connection", address)  # printing on server
            else:
                try:
                    data = client_socket.recv(1024).decode()  # receiving data
                    if data:
                        check_all(data, client_socket)  # checking data
                    else:
                        client_socket.close()  # closing client socket
                        print("Connection With Client Closed [closed login window]")
                        open_client_sockets.remove(client_socket)  # removing from the list

                except ConnectionResetError:  # Client Closed the chat window
                    try:
                        # we find his name by his socket
                        name = list(valid_users.keys())[list(valid_users.values()).index(client_socket)]
                        # and disconnecting him
                        disconnect(client_socket, name)

                    except (IndexError, ValueError) as e:  # client stopped console running
                        client_socket.close()  # closing client socket
                        print("Connection With Client Closed [closed login window]")
                        open_client_sockets.remove(client_socket)  # removing from the list

        broadcast()  # sending all the messages
