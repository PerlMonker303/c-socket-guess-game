import struct
import socket
import ctypes
import sys
import threading
import select
import time

'''
- client sends a ping to the server TCP to register
- create a thread that will listen for server inputs 
(when a client registered/left the server)
- messages will be sent through UDP to all clients stored in the client
'''

MAX_MSG_LEN = 100
addresses = []
usernames = []
hostname_glb = ""
port_glb = 0
username_glb = ""
s = 0 # socket of the client
disconnect_time = 5 # 5 seconds for disconnect
disconnecting = 0
socket_com = 0 # communication socket UDP

def sendMessage(msg):
    if len(msg) > MAX_MSG_LEN:
        print('Message is too long (max',MAX_MSG_LEN,')')
        return
    print('Sending message to users', addresses)
    for addrc in addresses:
        # send code = 4 (message)
        code = 4
        code_packed = struct.pack('!H',code)
        s.sendto(code_packed, addrc)
        # send length of username
        sz = len(username_glb) 
        sz_packed = struct.pack('!H',sz)
        s.sendto(sz_packed, addrc)
        # send username
        username_bytes = bytes(username_glb,'ascii')
        s.sendto(username_bytes, addrc) 
        # send length of message
        sz = len(msg)
        sz_packed = struct.pack('!H',sz)
        s.sendto(sz_packed, addrc)
        # send message
        msg_bytes = bytes(msg, 'ascii')
        s.sendto(msg_bytes, addrc)
        print('Sent')

def handleReceiveMessage():
    # thread that takes care of incoming messages from other users
    rlist = list()
    wlist = list()
    xlist = list()
    while 1:
        try:
            (rlistOut,wlistOut,xlistOut) = select(rlist,wlist,xlist)
        except:
            break
        if len(rlistOut) == 0 or disconnecting == 1:
            continue
        print('HRM_woke up')
        # read it from rlistOut
        socket = rlistOut.pop(0)
        # read code
        (code_packed, addr_sender) = socket.recvfrom(2)
        code = struct.unpack('!H', code_packed)
        if code != 4:
            print('CODE NOT 4')
            continue
        # read length of username
        (sz_packed, addr_sender) = socket.recvfrom(2)
        sz = struct.unpack(sz_packed)
        # read username
        (username_sender_bytes, addr_sender) = socket.recvfrom(sz)
        username_sender = bytes(username_sender_bytes, 'ascii')
        # read length of message
        (sz_packed, addr_sender) = socket.recvfrom(2)
        sz = struct.unpack(sz_packed)
        # read message
        (message_bytes, addr_sender) = socket.recvfrom(sz)
        message = bytes(message_bytes, 'ascii')
        print(username_sender,':',message)
        print('>',end='',flush=True)

def handleServer():
    # wait for server to send new client or remove a client
    rlist = list()
    rlist.append(s)
    wlist = list()
    xlist = list()
    xlist.append(s)
    while 1:
         # wait for code from the server - timeout
        try:
            (rlistOut, wlistOut, xlistOut) = select.select(rlist,wlist,xlist,disconnect_time)
        except:
            break
        if len(rlistOut) == 0 or disconnecting == 1:
            continue
        print('Woke up')
        #print(rlistOut)
        sc = rlistOut.pop(0)
        code_packed = sc.recv(2)
        try:
            code = struct.unpack('!H',code_packed)[0]
        except:
            print('SERVER FAILURE')
        if code == 1:
            # new user
            # receive ip length
            sz_packed = sc.recv(2)
            sz = struct.unpack('!H',sz_packed)[0]
            #print('iplen=',sz)
            # receive ip
            ip_bytes = sc.recv(sz)
            ip = ip_bytes.decode('ascii')
            #print('ip=',ip)
            # receive port
            port_packed = sc.recv(2)
            port = struct.unpack('!H',port_packed)[0]
            #print('port=',port)
            # receive username's length
            sz_packed = sc.recv(2)
            sz = struct.unpack('!H',sz_packed)[0]
            #print('usrlen=',sz)
            # receive username
            username_bytes = sc.recv(sz)
            username = username_bytes.decode('ascii')

            # remember address
            addr = (ip,port)
            addresses.append(addr)
            # remember username
            usernames.append(username)

            print(username,'joined the server.')
            print(addresses)
            print(usernames)
            print('>',end='',flush=True)
        elif code == 2:
            # disconnecting user
            # receive ip length
            sz_packed = sc.recv(2)
            sz = struct.unpack('!H',sz_packed)[0]
            #print('iplen=',sz)
            # receive ip
            ip_bytes = sc.recv(sz)
            ip = ip_bytes.decode('ascii')
            #print('ip=',ip)
            # receive port
            port_packed = sc.recv(2)
            port = struct.unpack('!H',port_packed)[0]
            #print('port=',port)
            # receive username's length
            sz_packed = sc.recv(2)
            sz = struct.unpack('!H',sz_packed)[0]
            #print('usrlen=',sz)
            # receive username
            username_bytes = sc.recv(sz)
            username = username_bytes.decode('ascii')

            # remove address
            addr = (ip,port)
            addresses.remove(addr)
            
            # remove username
            usernames.remove(username)

            print(username,'left the server.')
            print(addresses)
            print(usernames)
            print('>',end='',flush=True)
        else:
            print(code)
            print('Invalid code: handleServer')


if __name__ == "__main__":
    # create socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # TCP for registration/unsubscribing

    # parse arguments from cli
    hostname = str(sys.argv[1])
    hostname_glb = hostname
    port = int(sys.argv[2])
    port_glb = port
    username = str(sys.argv[3])
    username_glb = username

    # connect to server
    try:
        s.connect((hostname,port))
        print('Connected to server')
    except socket.error as msg:
        print("Error: ",msg.strerror)
        exit(-1)

    # send code for registration
    code = 1
    code_packed = struct.pack('!H', code)
    s.send(code_packed)
    # send length
    sz = len(username)
    sz_packed = struct.pack('!H', sz)
    s.send(sz_packed)
    # send username
    username_bytes = bytes(username, 'ascii')
    s.send(username_bytes)

    # create a new UDP socket for client communication
    socket_com = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_com.bind(('0.0.0.0',0))

    # send the port of the new socket
    print('MY SOCKET PORT TO SERVER:',s.getsockname())
    print('MY SOCKET PORT TO CLIENTS:',socket_com.getsockname())
    port_sock = socket_com.getsockname()[1]
    port_sock_packed = struct.pack('!H',port_sock)
    s.send(port_sock_packed)

    # wait for response
    resp_packed = s.recv(2)
    resp = struct.unpack('!H', resp_packed)[0]
    print('Response:',resp)
    if resp == 1:
        # receive the no of addresses (clients) already registered
        no_addrc_packed = s.recv(2)
        no_addrc = struct.unpack('!H',no_addrc_packed)[0]
        for i in range(0,no_addrc):
            # receive the size of ip
            sz_packed = s.recv(2)
            sz = struct.unpack('!H',sz_packed)[0]
            # receive the ip
            ip_bytes = s.recv(sz)
            ip = ip_bytes.decode('ascii')
            # receive the port
            port_packed = s.recv(2)
            port = struct.unpack('!H',port_packed)[0]
            # receive the username length
            sz_packed = s.recv(2)
            sz = struct.unpack('!H',sz_packed)[0]
            # receive the username
            username_bytes = s.recv(sz)
            username = username_bytes.decode('ascii')
            # store the address
            addrc = (ip,port)
            addresses.append(addrc)
            # store the username
            usernames.append(username)

        print(addresses)
        print(usernames)
        print("Successfully registered. Welcome",username_glb)
    elif resp == 2:
        print("Username taken, failed to register")
        s.close()
        sys.exit()

    # create thread to listen for server changes (new clients)
    t = threading.Thread(target=handleServer)
    t.start()

    # create thread to listen for messages
    t_messages = threading.Thread(target=handleReceiveMessage)
    t_messages.start()

    # stay connected - send messages
    while 1:
        inp = str(input('>'))
        code = 1 # send a message to other clients
        if inp == '\d':
            code = 2 # unsubscribe from the server
        
        if code == 1:
            # send message to other users using UDP
            sendMessage(inp)
        else:
            # unsubscribe - talk to the server about it
            disconnecting = 1 # mark that we are disconnecting
            code_packed = struct.pack('!H', code)
            print('Sending code',code,'for disconnect')
            s.send(code_packed)
            print('Sent')
            # wait for confirmation
            code_packed = s.recv(2)
            code = struct.unpack('!H',code_packed)[0]
            if code == 1:
                print('Disconnecting from server ... (eta: <',disconnect_time,'seconds)')
                s.close()
                socket_com.close()
                t.join()
                t_messages.join()
                print('Disconnected. Goodbye!')
                sys.exit()
            else:
                print('Could not disconnect. Try again at a later time.')

    # close socket
    s.close()