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
            data_addr, msg = PuncherProtocol.unpack(data)
            print("[Puncher] Connection from %s:%d" % c_pub_addr)
            print((data_addr, msg))
            
            if msg == 'H':
                c_prv_addr = data_addr
                print("ACK pub_addr")
                print((c_pub_addr, 'A'))
                print("Detected Private IP %s" % str(c_prv_addr))
                client_lookup[c_pub_addr[0]] = c_pub_addr
                sockfd.sendto(PuncherProtocol.pack(c_pub_addr, 'A'), c_pub_addr)
            elif msg == "C":
                target_addr = data_addr
                print("CONN node_addr")
                print(client_lookup)
                target_addr = client_lookup[target_addr[0]]
                print((target_addr, 'A'))
                sockfd.sendto(PuncherProtocol.pack(target_addr, 'A'), c_pub_addr)
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
        self.client = WeaklingClient(consumerQueue, apuncher_addr)
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
            self.queue.put((data, addr))
    def start(self):
        my_addr = socket.gethostbyname(socket.gethostname()),0
        print("HELLO my_addr")
        print(my_addr)

        self.sockfd.sendto(PuncherProtocol.pack(my_addr, 'H'), self.apuncher_addr)
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
    class Connection(object):
        def __init__(self, addr, sock):
            self.addr = addr
            self.sock = sock
        def send(self, data):
            self.sock.sendto(data, self.addr)
            self.sock.sendto(data, self.addr)
    def __init__(self, queue, apuncher_addr):
        self.queue = queue
        self.apuncher_addr = apuncher_addr
        self.sockfd = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        self.conn_cache = {}
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
    def connect(self, node_id, node_port=0):
        node_addr = (node_id, node_port)
        self.sockfd.sendto(PuncherProtocol.pack(node_addr, 'C'), self.apuncher_addr)
        data, addr = self.sockfd.recvfrom(PuncherProtocol.payload_len)
        node_addr, msg = PuncherProtocol.unpack(data)
        print("ACK node_addr")
        print(node_addr)
        print("Connect to node")
        return WeaklingClient.Connection(node_addr, self.sockfd)
    def start(self):
        self.t.start()

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
            data, addr = item
            data = data.decode('utf-8')
            print("Recieved [%s]" % data)
            if data == "Send me chunk 1.":
                print("\nSending back")
                conn = self.weaklingP.client.connect(*addr)
                conn.send("Here is chunk 1.".encode('utf-8'))
    def start(self):
        self.t.start()
        self.weaklingP.start()
    def shutdown(self):
        print("Put None")
        self.p_queue.put(None)
        self.weaklingP.shutdown()
        #self.t.join(1)
    def get_input(self):
        while True:
            print('Dodgy>', end='', flush=True)
            data = sys.stdin.readline()
            if data == 'Q':
                break
            addr_raw = data.split(',')
            addr = (addr_raw[0], int(addr_raw[1]))
            print("Connecting to %s" % str(addr))
            conn = self.weaklingP.client.connect(*addr)
            conn.send("Send me chunk 1.".encode('utf-8'))
#            conn.send("HELLO WORLD".encode('utf-8'))
            
            # Now we send data
            
            #self.c_queue.put(data)

class DirectoryServer(object):
    def __init__(self):
        pass
class DirectoryClient(object):
    def __init__(self):
        pass
    def list(self):
        return [("Hello.txt", 50121), ("Hello1.txt", 50122)]
    def new_file(self, file_name, chunk_list):
        return True

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
