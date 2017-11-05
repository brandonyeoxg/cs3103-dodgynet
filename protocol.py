from ctypes import *
import socket
import socketserver
import re
import logging
import threading

def pack(obj):
    buf = string_at(byref(obj), sizeof(obj))
    return buf
def unpack(buf, Type):
    cstring = create_string_buffer(buf)
    obj = cast(pointer(cstring), POINTER(Type)).contents
    return obj
def pack_ip(obj):
    return (c_ubyte*4)(*(socket.inet_aton(obj)))
def unpack_ip(bin_arr):
    return socket.inet_ntoa(bytearray(bin_arr))
def pack_str(obj, size):
    return obj.encode('utf-8')
    bytes = obj.encode('utf-8')
    return (c_ubyte*size)(*(bytes))
def unpack_str(bin_arr, size):
    bytes_arr = bytearray(bin_arr)
    return bytes_arr.decode('utf-8')
def unpack_str_s(bin_arr, size, actual_size):
    return unpack_str(bin_arr, size)[:actual_size]
    
def b2cb(bytes, size):
    return (c_ubyte * size)(*(bytes))
def cb2b(c_bytes):
    return bytearray(c_bytes)

def debug_hex(bin_arr):
    hex_str = hex(bin_arr)
    return re.sub(r'(:00)+', ':*', hex_str)
def hex(bytes, delim=':'):
    return delim.join(format(x, '02x') for x in bytes).upper()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True
    def __init__(self, addr, RequestHandlerClass, Type):
        socketserver.TCPServer.__init__(self, addr, RequestHandlerClass)
        self.Type = Type
        self.size = sizeof(Type())
    def serve_forever_nb(self):
        th = threading.Thread(target=self.serve_forever)
        th.daemon = True
        th.start()
        
class UDPServer(socketserver.UDPServer):
    allow_reuse_address = True
    def __init__(self, addr, RequestHandlerClass, Type):
        socketserver.UDPServer.__init__(self, addr, RequestHandlerClass)
        self.Type = Type
        self.size = sizeof(Type())
    def serve_forever_nb(self):
        th = threading.Thread(target=self.serve_forever)
        th.daemon = True
        th.start()

class TCPClient(object):
    def __init__(self, addr, Type):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = addr
        self.socket.connect(addr)
        self.size = sizeof(Type())
        self.Type = Type
    def send(self, obj):
        bin_arr = pack(obj)
        logging.debug("Client sent: %s" % debug_hex(bytearray(bin_arr)))
        self.socket.sendall(bin_arr)
    def recv(self):
        bin_arr = self.socket.recv(self.size)
        logging.debug("Client recv: %s" % debug_hex(bin_arr))
        return unpack(bin_arr, self.Type)
    def close(self):
        logging.debug("Closing socket.")
        self.socket.close()

class UDPClient(object):
    def __init__(self, addr, Type):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.set_type(addr, Type)
    def set_type(self, addr, Type):
        self.addr = addr
        self.size = sizeof(Type())
        self.Type = Type
    def send(self, obj):
        bin_arr = pack(obj)
        logging.debug("Client sent: %s to %s" % (debug_hex(bytearray(bin_arr)), "%s:%d"%self.addr) )
        self.socket.sendto(bin_arr, self.addr)
    def recv(self):
        bin_arr, addr = self.socket.recvfrom(self.size)
        logging.debug("Client recv: %s from %s" % (debug_hex(bin_arr), "%s:%d"%addr))
        return unpack(bin_arr, self.Type)
    def close(self):
        logging.debug("Closing socket.")
        self.socket.close()

class Handler(socketserver.BaseRequestHandler):
    def setup(self):
        pass
    def handle(self):
        pass
    def finish(self):
        pass
    def send(self, obj):
        bin_arr = pack(obj)
        logging.debug("Server sent: %s" % debug_hex(bytearray(bin_arr)))
        self.request.sendall(bin_arr)
    def recv(self):
        bin_arr = self.request.recv(self.server.size)
        logging.debug("Server recv: %s" % debug_hex(bin_arr))
        return unpack(bin_arr, self.server.Type)
        
class UDPHandler(socketserver.BaseRequestHandler):
    def send_back(self, obj):
        self.send(obj, self.client_address)
    def send(self, obj, addr):
        bin_arr = pack(obj)
        logging.debug("Server sent to %s: %s" % ("%s:%d"%addr, debug_hex(bytearray(bin_arr))))
        self.request[1].sendto(bin_arr, addr)
    def recv(self):
        bin_arr = self.request[0]
        logging.debug("Server recv: %s" % debug_hex(bin_arr))
        return unpack(bin_arr, self.server.Type)

class Packet(Structure):
    _fields_ = [("id", c_ubyte * 4),
                ("ce", c_ubyte),
                ("ip", c_ubyte * 4)]

'''
p = Packet()
p.id = pack_str("H", 4)
p.ip = pack_ip('255.255.255.255')

print(sizeof(p))

# cast the struct to a pointer to a char array
pdata = pack(p)
# now you can just save/send the struct data
#dd = pdata.contents.raw
print(pdata)

p = unpack(pdata, Packet)
print(unpack_str(p.id, 4))
print(p.ce)
print(unpack_ip(p.ip))
'''
# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
