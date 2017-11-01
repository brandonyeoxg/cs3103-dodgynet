import protocol
import ctypes as ct

class DirPacket(ct.Structure):
    _fields_ = [("id", ct.c_int),
                ("ip", ct.c_int)]

p = DirPacket()
p.id = 123
p.ip = 456
packed = protocol.pack(p)
unpacked = protocol.unpack(packed,DirPacket)
print(protocol.debug_hex(bytearray(protocol.pack(p))))
print(unpacked.id)
print(unpacked.ip)

s = DirPacket()
s.id = 0
s.ip = 2
print(protocol.debug_hex(bytearray(protocol.pack(s))))

class DirServer(protocol.ThreadedTCPServer):
    def __init__(self, addr=('', 50817)):
        protocol.ThreadedTCPServer.__init__(self, addr, DirHandler, DirPacket)
        self.arg = []

class DirClient(protocol.TCPClient):
    def __init__(self):
        protocol.TCPClient.__init__(self, ('localhost', 50817), DirPacket)

class DirHandler(protocol.Handler):
    def setup(self):
        print("Connection received from %s" % str(self.client_address))
        ppp = DirPacket()
        ppp.id = 123
        ppp.ip = 456
        packed = protocol.pack(ppp)
        unpacked = protocol.unpack(packed,DirPacket)
        print(protocol.debug_hex(bytearray(protocol.pack(ppp))))
        print(unpacked.id)
        print(unpacked.ip)
        print(protocol.debug_hex(bytearray(protocol.pack(unpacked))))
        self.send(ppp)
    def handle(self):
        while True:
            print(self.server.arg)
            # self.request is the TCP socket connected to the client
            self.data = self.recv()
            self.server.arg.append(self.data.id)
            if protocol.unpack(self.data.ip) == "QQQQ":
                break
            print("{} wrote:".format(self.client_address[0]))
            print(self.id)
            # just send back the same data, but upper-cased
            self.request.sendall(s)
    def finish(self):
        self.request.sendall(s)

if __name__ == "__main__":

    # Create the server, binding to localhost on port 9999
    server = DirServer()

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.shutdown()

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
