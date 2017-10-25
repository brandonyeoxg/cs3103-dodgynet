"""
Puncher, both a client and server. It will start the server when the Puncher 
object is initialized. We will assume that all strings are validated.
"""
import Config
import socket
import struct

class PuncherProtocol(object):
    payload_len = 56
    def __init__(self, host, port, server_bufsize, client_bufsize, timeout):
        # Start the server here
        self.server = PuncherServer(host, port, timeout)
    def shutdown(self):
        pass
    @classmethod
    def pack(cls, addr, msg):
        ip, port = addr
        # IP is 32 bit data
        data = socket.inet_aton(ip)
        # port is a 16 bit data
        data += struct.pack("H", port)
        # msg is either:
        #   H - hello
        #   C - connect
        #   A - ack
        data += struct.pack("c", msg.encode("utf-8"))
        return data
    @classmethod
    def unpack(cls, data):
        host = socket.inet_ntoa(data[:4])
        port, = struct.unpack("H", data[4:6])
        msg, = struct.unpack("c", data[6:7])
        return (host,port), msg.decode("utf-8")

class PuncherServer(object):
    def __init__(self, host, port, timeout):
        self.addr = ( host, port )
        self.start()
        self.t.daemon = True
    def start(self):
        # We start the UDP listener
        sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sockfd.bind( self.addr )
        print("[Puncher] Listening on UDP[%d]" % self.addr[1])

        # Now we keep serving clients
        client_lookup = {}
        while True:
            data, c_pub_addr = sockfd.recvfrom(PuncherProtocol.payload_len)
            c_prv_addr, msg = PuncherProtocol.unpack(data)
            print("[Puncher] Connection from %s:%d" % c_pub_addr)
            print((c_prv_addr, msg))
            
            if msg == 'H':
                print("ACK pub_addr")
                print((c_pub_addr, 'A'))
                client_lookup[c_pub_addr[0]] = c_pub_addr
                sockfd.sendto(PuncherProtocol.pack(c_pub_addr, 'A'), c_pub_addr)
            '''
            data, addr = sockfd.recvfrom(PuncherProtocol.payload_len)
            if data != "ok".encode('utf-8'):
                continue
            
            print("[Puncher] Pool ID %s" % pool)
            try:
                a, b = poolqueue[pool], addr
                sockfd.sendto( PuncherProtocol.pack(a, 'A'), b )
                sockfd.sendto( PuncherProtocol.pack(b, 'A'), a )
                print("[Puncher] linked PID %s" % pool)
                del poolqueue[pool]
            except KeyError:
                poolqueue[pool] = addr

            data.strip()
            '''
    def shutdown(self):
        # kill
        pass	

class WeaklingProtocol(object):
    def __init__(self, apuncher_addr, producerQueue, consumerQueue):
        self.server = WeaklingServer(apuncher_addr, producerQueue)
        self.client = WeaklingClient(consumerQueue)
    def shutdown(self):
        self.server.shutdown()
        self.client.shutdown()
    def start(self):
        self.server.start()
        self.client.start()

import sys
class WeaklingServer(object):
    def __init__(self, apuncher_addr, queue):
        self.queue = queue
        self.apuncher_addr = apuncher_addr
        self.sockfd = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        self.t = threading.Thread(target=self.thread_job)
        self.t.daemon = True
    def thread_job(self):
        while True:
            print("[WeaklingServer] Listening...")
            data, addr = self.sockfd.recvfrom(1024)
            print((data, addr))
            self.queue.put(data.decode('utf-8'))
    def start(self):
        master = self.apuncher_addr

        my_addr = socket.gethostbyname(socket.gethostname()),0
        print("HELLO my_addr")
        print(my_addr)

        self.sockfd.sendto(PuncherProtocol.pack(my_addr, 'H'), master)
        data, addr = self.sockfd.recvfrom(PuncherProtocol.payload_len)
        my_addr, msg = PuncherProtocol.unpack(data)
        print("ACK my_addr")
        print(my_addr)

        if msg != 'A':
            print("Server Message fatal error.")
            sys.exit(1)

        self.t.start()
    def shutdown(self):
        #self.t.terminate()
        #self.t.join()
        print("Socket Shutdown")
        #my_addr = socket.gethostbyname(socket.gethostname()),0
        #self.sockfd.sendto(None, my_addr)
        self.sockfd.close()
'''
    def recv_unpack():
        data, addr = sock.recvfrom(PuncherProtocol.payload_len)
        my_addr, msg = PuncherProtocol.unpack(data)
    def pack_send(sock, data, dst_addr):
        sock.sendto(PuncherProtocol.pack(*data), dst_addr)
'''
class WeaklingClient(object):
    def __init__(self, queue):
        self.queue = queue
        self.t = threading.Thread(target=self.thread_job)
        self.t.daemon = True
    def shutdown(self):
        self.queue.put(None)
    def thread_job(self):
        while True:
            item = self.queue.get()
            if item == None:
                print("Quit WeaklingClient")
                break
            self.sockfd.sendto( item.encode('utf-8'), self.target )
    def start(self):
        pass
        #self.t.start()

import queue
import threading
class DummyEndpoint(object):
    def __init__(self, apuncher_addr):
        self.p_queue = queue.Queue()
        self.c_queue = queue.Queue()
        self.weaklingP = WeaklingProtocol(apuncher_addr, self.p_queue, self.c_queue)
        self.t = threading.Thread(target=self.thread_job)
        self.t.daemon = True
    def thread_job(self):
        while True:
            item = self.p_queue.get()
            if item == None:
                print("Quit Dummy Endpoint")
                break
            sys.stdout.write(item)
    def start(self):
        #self.t.start()
        self.weaklingP.start()
    def shutdown(self):
        print("Put None")
        self.p_queue.put(None)
        self.weaklingP.shutdown()
        #self.t.join(1)
    def get_input(self):
        while True:
            data = sys.stdin.readline()
            if data == 'Q':
                break
            self.c_queue.put(data)

class DirectoryServer(object):
    def __init__(self):
        pass
class DirectoryClient(object):
    def __init__(self):
        pass
    def list(self):
        return [("Hello.txt", 50121), ("Hello1.txt", 50122)]
    def new_file(self):
        return True

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
