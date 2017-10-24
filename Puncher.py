"""
Puncher, both a client and server. It will start the server when the Puncher 
object is initialized. We will assume that all strings are validated.
"""
import Config
import socket
import struct

class PuncherProtocol(object):
    def __init__(self, host, port, server_bufsize, client_bufsize, timeout):
        # Start the server here
        self.server = PuncherServer(host, port, timeout)
    def shutdown(self):
        pass

class PuncherServer(object):
    def __init__(self, host, port, timeout):
        self.addr = ( host, port )
        self.start()
    def start(self):
        # We start the UDP listener
        sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sockfd.bind( self.addr )
        print("[Puncher] Listening on UDP[%d]" % self.addr[1])

        # Now we keep serving clients
        client_lookup = {}
        poolqueue = {}
        while True:
            data, addr = sockfd.recvfrom(64)
            print("[Puncher] Connection from %s:%d" % addr)
            
            # Check for the type of message, can be hello or connect
            pool = data.strip().decode('UTF-8')
            # Send OK message
            sockfd.sendto(("ok "+pool).encode('utf-8'), addr )
            
            data, addr = sockfd.recvfrom(2)
            if data != "ok".encode('utf-8'):
                continue
            
            print("[Puncher] Pool ID %s" % pool)
            try:
                a, b = poolqueue[pool], addr
                sockfd.sendto( PuncherServer.pack(a, 'A'), b )
                sockfd.sendto( PuncherServer.pack(b, 'A'), a )
                print("[Puncher] linked PID %s" % pool)
                del poolqueue[pool]
            except KeyError:
                poolqueue[pool] = addr

            data.strip()
    @classmethod
    def pack(cls, addr, msg):
        ip, port = addr
        # IP is 32 bit data
        data = socket.inet_aton(ip)
        # port is a 16 bit data
        data += struct.pack("H", port)
        return data
    @classmethod
    def unpack(cls, data):
        host = socket.inet_ntoa(data[:4])
        port, = struct.unpack("H", data[-2:])
        return host, port
    def shutdown(self):
        # kill
        pass	

class WeaklingProtocol(object):
    def __init__(self, apuncher_addr, queue):
        self.server = WeaklingServer(apuncher_addr, queue)
        self.client = WeaklingClient()
    def shutdown(self):
        self.server.shutdown()
        self.client.shutdown()
    def start(self):
        self.server.start()
        self.client.start()

from select import select
import sys
class WeaklingServer(object):
    def __init__(self, apuncher_addr, queue):
        self.queue = queue
        self.apuncher_addr = apuncher_addr
        self.t = threading.Thread(target=self.thread_job)
    def thread_job(self):
        while True:
            rfds,_,_ = select( [0, self.sockfd], [], [] )
            if 0 in rfds:
                data = sys.stdin.readline()
                if not data:
                    break
                self.sockfd.sendto( data.encode('utf-8'), self.target )
            elif self.sockfd in rfds:
                data, addr = self.sockfd.recvfrom( 1024 )
                self.queue.put(data.decode('utf-8'))
    def start(self):
        pool = '1'
        master = self.apuncher_addr
        self.sockfd = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        self.sockfd.sendto(pool.encode('utf-8'), master)
        data, addr = self.sockfd.recvfrom( len(pool)+3 )

        if data != ("ok "+pool).encode('utf-8'):
            print("unable to request!")
            sys.exit(1)
        self.sockfd.sendto( "ok".encode('utf-8'), master )
        print("request sent, waiting for partner in pool '%s'..." % pool)
        data, addr = self.sockfd.recvfrom( 6 )

        self.target = PuncherServer.unpack(data)
        print("connected to %s:%d" % self.target)
        self.t.start()
    def shutdown(self):
        #self.t.terminate()
        #self.t.join()
        print("Socket Shutdown")
        self.sockfd.close()

class WeaklingClient(object):
    def __init__(self):
        pass
    def shutdown(self):
        pass
    def start(self):
        pass

import queue
import threading
class DummyEndpoint(object):
    def __init__(self, apuncher_addr):
        self.queue = queue.Queue()
        self.weaklingP = WeaklingProtocol(apuncher_addr, self.queue)
        self.t = threading.Thread(target=self.thread_job)
    def thread_job(self):
        while True:
            item = self.queue.get()
            if item == None:
                print("No Item")
                break
            sys.stdout.write(item)
    def start(self):
        self.t.start()
        self.weaklingP.start()
    def shutdown(self):
        print("Put None")
        self.queue.put(None)
        self.weaklingP.shutdown()
        #self.t.join(1)

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
