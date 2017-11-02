from ctypes import *
import socket
import socketserver

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
    bytes = obj.encode('utf-8')
    return (c_ubyte*size)(*(bytes))
def unpack_str(bin_arr, size):
    bytes_arr = bytearray(bin_arr)
    return bytes_arr.decode('utf-8')
def debug_hex(bin_arr):
    return ':'.join(format(x, '02x') for x in bin_arr).upper()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True
    def __init__(self, addr, RequestHandlerClass, Type):
        socketserver.TCPServer.__init__(self, addr, RequestHandlerClass)
        self.Type = Type
        self.size = sizeof(Type())

class TCPClient(object):
    def __init__(self, addr, Type):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(addr)
        self.size = sizeof(Type())
        self.Type = Type
    def send(self, obj):
        bin_arr = pack(obj)
        print(debug_hex(bytearray(bin_arr)))
        self.socket.sendall(bin_arr)
    def recv(self):
        bin_arr = self.socket.recv(self.size)
        print(debug_hex(bin_arr))
        return unpack(bin_arr, self.Type)
    def close(self):
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
        print(debug_hex(bytearray(bin_arr)))
        self.request.sendall(bin_arr)
    def recv(self):
        bin_arr = self.request.recv(self.server.size)
        print(debug_hex(bin_arr))
        return unpack(bin_arr, self.server.Type)

class Packet(Structure):
    _fields_ = [("id", c_ubyte * 4),
                ("ce", c_ubyte),
                ("ip", c_ubyte * 4)]

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

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
