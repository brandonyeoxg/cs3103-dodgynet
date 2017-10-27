"""
Puncher, both a client and server. It will start the server when the Puncher 
object is initialized. We will assume that all strings are validated.
"""
import Config
import socket
import struct
import datetime
from collections import defaultdict

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
    def start(self):
        # We start the UDP listener
        sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sockfd.bind( self.addr )
        print("[Puncher] Listening on UDP[%d]" % self.addr[1])

        # Now we keep serving clients
        client_lookup = defaultdict(dict)
        while True:
            data, c_pub_addr = sockfd.recvfrom(PuncherProtocol.payload_len)
            data_addr, msg = PuncherProtocol.unpack(data)
            print("[Puncher] Recieve Data[%s] from %s" % (str((data_addr, msg)), str(c_pub_addr)))
            
            if msg == 'H':
                c_prv_addr = data_addr
                data = (c_pub_addr, 'A')
                print("[Puncher] Send ACK pub_addr[%s] to [%s]" % (str(data), str(c_pub_addr)))
                client_lookup[c_pub_addr[0]][c_pub_addr[1]] = c_pub_addr + (datetime.datetime.now(), )
                sockfd.sendto(PuncherProtocol.pack(*data), c_pub_addr)
            elif msg == "C":
                target_addr = data_addr
                if target_addr[1]==0:
                    vals = list(client_lookup[target_addr[0]].values())
                    target_addr = min(vals, key = lambda t: t[2])
                    target_addr = target_addr[0:2]
                data = (target_addr, 'A')
                print("[Puncher] Send CONN target_addr[%s] to [%s]" % (str(data), str(c_pub_addr)))
                sockfd.sendto(PuncherProtocol.pack(*data), c_pub_addr)
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
        # HACK TODO
        self.client.my_addr = self.server.my_addr
        print("TODO, address [%s]" % str(self.client.my_addr))
    def get_identity(self):
        return self.server.get_identity()
    @classmethod
    def pack(cls, addr, app_data):
        ip, port = addr
        # IP is 32 bit data
        data = socket.inet_aton(ip)
        # port is a 16 bit data
        data += struct.pack("H", port)
        # len to capture the number of bytes
        data += struct.pack("H", len(app_data))
        # app_data is 1024 bits
        data += app_data
        print(''.join('{:02x}'.format(x) for x in app_data))
        print(len(app_data))
        return data
    @classmethod
    def unpack(cls, data):
        host = socket.inet_ntoa(data[:4])
        port, = struct.unpack("H", data[4:6])
        app_len, = struct.unpack("H", data[6:8])
        app_data = data[8:8+app_len]
        print(''.join('{:02x}'.format(x) for x in app_data))
        print(len(data[8:8+app_len]))
        return (host,port), app_data

import sys
class WeaklingServer(object):
    def __init__(self, apuncher_addr, queue):
        self.queue = queue
        self.apuncher_addr = apuncher_addr
        self.sockfd = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        self.t = threading.Thread(target=self.thread_job)
        self.t.daemon = True
        self.id = "Dodgy"
    def thread_job(self):
        while True:
            data, addr = self.sockfd.recvfrom(1030) # 1024+6
            r_addr, app_data = WeaklingProtocol.unpack(data)
            print("[Weakling-S] Recieve Data from %s, send back %s" % (str(addr), str(r_addr)))
            self.queue.put((app_data, r_addr))
    def start(self):
        my_addr = (socket.gethostbyname(socket.gethostname()),0)
        print("[Weakling-S] Send HELLO my_addr[%s] to %s" % (str(my_addr), str(self.apuncher_addr)))
        self.sockfd.sendto(PuncherProtocol.pack(my_addr, 'H'), self.apuncher_addr)
        data, addr = self.sockfd.recvfrom(PuncherProtocol.payload_len)
        my_addr, msg = PuncherProtocol.unpack(data)
        print("[Weakling-S] Recieve Data[%s] from %s" % (str((my_addr, msg)), str(addr)))

        if msg != 'A':
            print("[Weakling-S] Server Message fatal error.")
            sys.exit(1)
        self.id = "%s:%d" % my_addr
        self.my_addr = my_addr
        self.t.start()
    def get_identity(self):
        return self.id
    def shutdown(self):
        #self.t.terminate()
        #self.t.join()
        print("[Weakling-S] Socket Shutdown")
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
        def __init__(self, my_addr, addr, sock):
            self.my_addr = my_addr
            self.addr = addr
            self.sock = sock
        def send(self, app_data):
            print("[Weakling-C-C] Send App-Data[%s] to %s" % (str(app_data), str(self.addr)))
            #self.my_addr
            data = WeaklingProtocol.pack(self.my_addr, app_data)
            self.sock.sendto(data, self.addr)
            self.sock.sendto(data, self.addr)
    def __init__(self, queue, apuncher_addr):
        self.queue = queue
        self.apuncher_addr = apuncher_addr
        self.sockfd = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        self.conn_cache = {}
        #self.t = threading.Thread(target=self.thread_job)
        #self.t.daemon = True
    def shutdown(self):
        self.queue.put(None)
    def thread_job(self):
        while True:
            item = self.queue.get()
            if item == None:
                print("[Weakling-C] Stop Queue")
                break
            #self.sockfd.sendto( item.encode('utf-8'), self.target )
    def connect(self, node_id, node_port=0):
        node_addr = (node_id, node_port)
        if node_port != 0:
            return WeaklingClient.Connection(self.my_addr, node_addr, self.sockfd)
        print("[Weakling-C] Send CONN my_addr[%s] to %s" % (str(node_addr), str(self.apuncher_addr)))
        self.sockfd.sendto(PuncherProtocol.pack(node_addr, 'C'), self.apuncher_addr)
        data, addr = self.sockfd.recvfrom(PuncherProtocol.payload_len)
        node_addr, msg = PuncherProtocol.unpack(data)
        print("[Weakling-C] Recieve Data[%s] from %s" % (str((node_addr, msg)), str(addr)))
        return WeaklingClient.Connection(self.my_addr, node_addr, self.sockfd)
    def start(self):
        #self.t.start()
        pass

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
            print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
            if item == None:
                print("[Client] Endpoint Terminate")
                break
            data, addr = item
            data = data.decode('utf-8')
            print("[Client] Data Unpacked: %s" % data)
            if data == "Send me chunk 1.":
                print("[Client] Send Data[Here is chunk 1.]")
                conn = self.weaklingP.client.connect(addr[0])
                conn.send("Here is chunk 1.".encode('utf-8'))
    def start(self):
        self.t.start()
        self.weaklingP.start()
    def shutdown(self):
        print("[Client] Terminate Queue by put in None")
        self.p_queue.put(None)
        self.weaklingP.shutdown()
        #self.t.join(1)
    def get_input(self):
        while True:
            print(self.weaklingP.get_identity() + '>', end='', flush=True)
            data = sys.stdin.readline()
            if data == 'Q':
                break
            addr_raw = data.split(':')
            addr = (addr_raw[0], int(addr_raw[1]))
            print("[Client] Request chunk 1.")
            conn = self.weaklingP.client.connect(*addr)
            conn.send("Send me chunk 1.".encode('utf-8'))
#            conn.send("HELLO WORLD".encode('utf-8'))
            
            # Now we send data
            
            #self.c_queue.put(data)

from pathlib import Path

class DirectoryServer(object):
    def __init__(self):
        pass
class DirectoryClient(object):
    def __init__(self):
        pass
    def list(self):
        lock_file = Path("temp.lock")
        if lock_file.is_file():
            return [("demo.txt", 50121)]
        else:
            with open('temp.lock', 'w') as f:
                f.write("Hello")
        print("No files exist!")
        return []
    def new_file(self, file_name, chunk_list):
        return True

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
