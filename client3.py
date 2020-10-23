import struct
import socket
import ctypes
import sys
import threading

'''
- client sends a ping to the server TCP to register
- create a thread that will listen for server inputs 
(when a client registered/left the server)
- messages will be sent through UDP to all clients stored in the client
'''

clients_addresses = []
hostname_glb = ""
port_glb = 0
username_glb = ""
s = 0

myLock = threading.Lock()

def sendMessage(msg):
    for c in clients_addresses:
        ip = c[0]
        port = c[1]


def handleServer(hostname, port):
    # here we wait for server inputs
    while 1:
        code_packed = s.recv(2)
        code = struct.unpack('!H',code_packed)[0]
        if code == 1:
            ip = s.recvfrom(15).decode('ascii')
            port_packed = s.recvfrom(2)
            port = struct.unpack('!H',port_packed)
            print(ip,port)
            myLock.acquire(blocking=True)
            clients_addresses.append((ip,port))
            myLock.release()
    print('Handing server')

    print('Done')


if __name__ == "__main__":
    # create socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # TCP for registrations/unsubscribing

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

    # send username
    code = 1 # code for registration
    code_packed = struct.pack('!H', code)
    s.send(code_packed)
    # send length
    sz = len(username)
    sz_packed = struct.pack('!H', sz)
    s.send(sz_packed)
    # send username
    username_bytes = bytes(username, 'ascii')
    s.send(username_bytes)

    # wait for response
    resp_packed = s.recv(2)
    resp = struct.unpack('!H', resp_packed)[0]
    if resp == 1:
        print("Successfully registered. Welcome!")
    elif resp == 2:
        print("Username taken, failed to register")
        s.close()
        sys.exit()

    # create thread to listen for server changes
    #t = threading.Thread(target=handleServer, args=(hostname, port))
    #t.start()

    # stay connected - send messages
    while 1:
        inp = str(input('>'))
        code = 1 # send a message to other clients
        if inp == '\s':
            code = 2 # unsubscribe from the server
        
        if code == 1:
            # send message to other users using UDP
            pass
        else:
            # unsubscribe - talk to the server about it
            code_packed = struct.pack('!H', code)
            s.send(code_packed)
            print("Disconnected. Goodbye!")
            break

        print('Sending message',inp)
        # send message to all clients
        sendMessage(inp)


    # close socket
    s.close()