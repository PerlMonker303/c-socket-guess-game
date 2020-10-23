import struct
import socket
import ctypes
import sys
import threading
import select

'''
- server receives TCP connections from clients to register them
- create a thread for receiving messages from clients
- for each new client the server will ping all other clients
- for each client who leaves the server - the same thing
'''

BACKLOG = 5
usernames = set()
addresses = set() # addresses of registered clients
sockets = set()

myLock = threading.Lock()
#e = threading.Event()
#e.clear()

'''
def alertClients(s_client, addrc):
    # tells other clients when a new client comes to the server
    # send the address in two parts: ip and port
    (ip, port) = addrc
    code = 1
    code_packed = struct.pack('!H', code)
    ip_bytes = bytes(ip, 'ascii')
    port_packed = struct.pack('!H', port)
    for s in sockets:
        s.send(code_packed)
        s.send(ip_bytes)
        s.send(port_packed)
'''
def handleClientsRequests():
    # waits for any client to reach the server with a special command
    # for now only disconnecting works
    rlist = sockets.copy()
    wlist = {}
    xlist = {}
    # add sockets to the readList
    while sockets.__len__() > 0:
        (rlistOut,wlistOut,xlistOut) = select.select(rlist,wlist,xlist)
        print('Woke up')
        print('before pop:',rlistOut)
        s_new = rlistOut.pop(0)
        print('After pop:',rlistOut)
        print('s_new:',s_new)

        # read code
        code_packed = s_new.recv(2)
        code = struct.unpack('!H', code_packed)[0]
        if code == 2:
            # unsubscribe this user
            sockets.remove(s_new)
            pass
        else:
            print('Invalid code')

        rlist = sockets.copy()

    '''

    myLock.acquire(blocking=True) # acquire the lock
    if not sockets.__contains__(s_client):
        sockets.append(s_client)
    myLock.release() # release the lock

    # alert other clients of this new client
    alertClients(s_client, addrc)

    #while 1:
    resp_bytes = s_client.recv(2) # this should not given an error - just wait
    resp = struct.unpack('!H', resp_bytes)[0]
    print(resp)
    if resp == 1:
        usr_len_packed = s_client.recv(2)
        usr_len = struct.unpack('!H', usr_len_packed)[0]
        print('len:',usr_len)
        username_bytes = s_client.recv(usr_len)
        username = username_bytes.decode('ascii')
        print('username:',username)

    print("Done")
    '''

if __name__ == "__main__":    
    # create socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    port = int(sys.argv[1])
    
    # bind server
    s.bind(('0.0.0.0',port))

    # listen for clients
    s.listen(BACKLOG)
    print("Server is running ...")

    while 1:
        # accept connections from clients
        (s_new, addrc) = s.accept()
        # a client wants to interract with the server
        resp_bytes = s_new.recv(2) # this should not give an error - just wait
        resp = struct.unpack('!H', resp_bytes)[0]
        print('Code:',resp)
        if resp == 1: # connect new client
            usr_len_packed = s_new.recv(2) # receive the username length
            usr_len = struct.unpack('!H', usr_len_packed)[0]
            username_bytes = s_new.recv(usr_len) # receive the username
            username = username_bytes.decode('ascii')
            print('username:',username)

            # check if the username is free or not
            code = 0
            if usernames.__contains__(username):
                # username taken
                # error code 2
                code = 2
                print('Username taken')
            else:
                # store new username
                usernames.add(username)
                # store the user's address
                addresses.add(addrc)
                # store the user's socket
                sockets.add(s_new)
                # code 1 - success
                code = 1
                # create a thread to use for registered clients
                # THERE SHOULD ONLY BE ONE THREAD TO LISTEN FOR CLIENTS COMMANDS
                # THINK ABOUT IT TOMMORROW
                t = threading.Thread(target=handleClientsRequests)
                t.start()

            # send the code
            code_packed = struct.pack('!H', code)
            s_new.send(code_packed)
        elif resp == 2:
            # check if user is stored (however he should be)
            if addresses.__contains__(addrc):
                code = 2 # error code
                print('User',addrc,'not registered. Failed to remove.')
            else:
                # delete the user
                addresses.remove(addrc)
                usernames.remove(username)
                code = 1
            # send response back
            code_packed = struct.pack('!H', code)
            s_new.send(code_packed)
        else:
            print('Invalid code given by client ',addrc)

        print('Addresses:',addresses)
        print('Usernames:',usernames)

    # close server socket
    s.close()
    
'''
Once you have established the connection and registered a user
start a thread to listen for incoming client's requests - disconnection from the chat app
'''