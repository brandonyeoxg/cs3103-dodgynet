import socket
from ctypes import *

class Protocol():
    @classmethod
    def pack(cls, obj):
        return cast(byref(obj), POINTER(c_char * sizeof(obj)))
    @classmethod
    def unpack(cls, bin_arr, Type):
        obj = Type()
        memmove(pointer(obj), bin_arr, sizeof(obj))
        return obj
    @classmethod
    def pack_ip(cls, obj):
        return (c_ubyte*4)(*(socket.inet_aton(obj)))
    @classmethod
    def unpack_ip(cls, bin_arr):
        return socket.inet_ntoa(bytearray(bin_arr))
    @classmethod
    def pack_str(cls, obj, size):
        bytes = obj.encode('utf-8')
        return (c_ubyte*size)(*(bytes))
    @classmethod
    def unpack_str(cls, bin_arr, size):
        bytes_arr = bytearray(bin_arr)
        return bytes_arr.decode('utf-8')

class Packet(Structure):
    _fields_ = [("id", c_ubyte * 4),
                ("ce", c_ubyte),
                ("ip", c_ubyte * 4)]

p = Packet()
p.id = Protocol.pack_str("H", 4)
p.ce = 255
p.ip = Protocol.pack_ip('255.255.255.255')

print(sizeof(p))

# cast the struct to a pointer to a char array
pdata = Protocol.pack(p)
# now you can just save/send the struct data
dd = pdata.contents.raw
print(':'.join(format(x, '02x') for x in dd).upper())

p = Protocol.unpack(pdata, Packet)
print(Protocol.unpack_str(p.id, 4))
print(p.ce)
print(Protocol.unpack_ip(p.ip))

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
