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
usernames = list()
addresses = list() # addresses of registered clients
sockets = list()

myLock = threading.Lock()
#e = threading.Event()
#e.clear()


def alertClients(code, current_socket, addrc, username):
    # alerts the connected clients about crucial information
    # code = 1 - new client connected
    # code = 2 - client disconnected
    # also pass the username for printing purposes
    print('--alertClients')
    if code not in[1,2]:
        print('Invalid code: alertClients')

    code_packed = struct.pack('!H',code) # pack code

    # get info about current client
    sz = len(addrc[0]) # len of ip
    sz_packed = struct.pack('!H',sz)
    print('AC_sz=',sz)
    ip_bytes = bytes(addrc[0], 'ascii') # ip
    print('AC_ip=',addrc[0])
    port = addrc[1] # port
    port_packed = struct.pack('!H',port)
    print('AC_port=',port)
    sz_user = len(username) # len of username
    sz_user_packed = struct.pack('!H',sz_user)
    username_bytes = bytes(username, 'ascii') # username
    print('AC_sz_user=',sz_user)
    print('AC_username=',username)
    print('AC_CODE=',code)
    if code == 1: # new client      
        # send info to all other clients
        for socket in sockets:
            if socket != current_socket: # not the socket of the new user
                socket.send(code_packed) # send code
                socket.send(sz_packed) # send ip len
                socket.send(ip_bytes) # send ip
                socket.send(port_packed) # send port             
                socket.send(sz_user_packed) # send username len
                socket.send(username_bytes) # send username

    elif code == 2: # client disconnected
        # send the address of leaving user and username
        for socket in sockets:
            if socket != current_socket:
                socket.send(code_packed) # send code
                socket.send(sz_packed) # send ip len
                socket.send(ip_bytes) # send ip
                socket.send(port_packed) # send port             
                socket.send(sz_user_packed) # send username len
                socket.send(username_bytes) # send username


def handleClientsRequests():
    # waits for any client to reach the server with a special command
    # for now only disconnecting works
    rlist = sockets.copy()
    wlist = list()
    xlist = list()
    # add sockets to the readList
    while sockets.__len__() > 0:
        (rlistOut,wlistOut,xlistOut) = select.select(rlist,wlist,xlist)
        print('T_Woke up')
        print(addresses)
        if len(addresses) == 0: # nothing to do here
            break
        for r in rlistOut: # we might get more requests at the same time
            #print('T_Before pop:',rlistOut)
            s_new = r
            rlistOut.pop(0)
            #print('T_After pop:',rlistOut)
            #print('T_s_new:',s_new)

            # read code
            code_packed = s_new.recv(2)
            if code_packed == b'':
                continue
            code = struct.unpack('!H', code_packed)[0]
            #print('T_RECEIVED CODE FOR DISCONNECT')
            if code == 2:
                # unsubscribe this user
                pos = sockets.index(s_new)
                sockets.remove(s_new)
                username = usernames[pos]
                usernames.remove(username)
                addrc = addresses[pos]
                addresses.remove(addrc)
                # send confirmation
                code_conf = 1 # okay
                code_packed = struct.pack('!H',code_conf)
                s_new.send(code_packed)
                # alert other clients
                alertClients(code, s_new, addrc, username)

            else:
                print('T_Invalid code - skipping')

        print(addresses)
        print(usernames)

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
    print("M_Server is running ...")

    while 1:
        # accept connections from clients
        (s_new, addrc) = s.accept()
        # a client wants to interract with the server
        resp_bytes = s_new.recv(2) # this should not give an error - just wait
        resp = struct.unpack('!H', resp_bytes)[0]
        print('M_Code:',resp)
        if resp == 1: # connect new client
            usr_len_packed = s_new.recv(2) # receive the username length
            usr_len = struct.unpack('!H', usr_len_packed)[0]
            username_bytes = s_new.recv(usr_len) # receive the username
            username = username_bytes.decode('ascii')
            print('M_username:',username)

            # check if the username is free or not
            code = 0
            if usernames.__contains__(username):
                # username taken
                # error code 2
                code = 2
                print('M_Username taken')
            else:
                # store new username
                usernames.append(username)
                # store the user's address
                addresses.append(addrc)
                # store the user's socket
                sockets.append(s_new)
                # code 1 - success
                code = 1
                
            # send the code
            code_packed = struct.pack('!H', code)
            s_new.send(code_packed)

            # if code is 1 then we also send the list of addresses of
            # all connected users
            if code == 1:
                # send the number of addresses
                no_addrc = len(addresses)-1
                no_addrc_packed = struct.pack('!H', no_addrc)
                s_new.send(no_addrc_packed)
                # send the addresses
                for addr in addresses:
                    if addr != addrc: # not the current client
                        print(addr)
                        # send the ip size
                        sz = len(addr[0])
                        sz_packed = struct.pack('!H',sz)
                        s_new.send(sz_packed)
                        # send the ip address
                        ip_bytes = bytes(addr[0], 'ascii')
                        s_new.send(ip_bytes)
                        # send the port
                        port_packed = struct.pack('!H',addr[1])
                        s_new.send(port_packed)
                        # send the username length
                        pos = addresses.index(addr)
                        username_cur = usernames[pos]
                        sz = len(username_cur)
                        sz_packed = struct.pack('!H',sz)
                        s_new.send(sz_packed)
                        #send the username
                        username_bytes = bytes(username_cur, 'ascii')
                        s_new.send(username_bytes)

                # alert existing clients of this new client
                print('---',username)
                alertClients(code,s_new,addrc,username)

                # create a thread to use for registered clients
                # THERE SHOULD ONLY BE ONE THREAD TO LISTEN FOR CLIENTS COMMANDS
                # THINK ABOUT IT TOMMORROW
                t = threading.Thread(target=handleClientsRequests)
                t.start()

        elif resp == 2:
            # check if user is stored (however he should be)
            if addresses.__contains__(addrc):
                code = 2 # error code
                print('M_User',addrc,'not registered. Failed to remove.')
            else:
                # delete the user
                addresses.remove(addrc)
                usernames.remove(username)
                code = 1
            # send response back
            code_packed = struct.pack('!H', code)
            s_new.send(code_packed)
        else:
            print('M_Invalid code given by client ',addrc)

        print('M_Addresses:',addresses)
        print('M_Usernames:',usernames)

    # close server socket
    s.close()
    
'''
Once you have established the connection and registered a user
start a thread to listen for incoming client's requests - disconnection from the chat app
'''