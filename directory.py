
class DirectoryProtocol(object):
    @classmethod
    def pack(cls, dataBytes, chunkNum):
        pass
    @classmethod
    def unpack(cls, data):
        pass

class DirectoryServer(object):
    def serve_fore(self):
        pass
    def shutdown(self):
        pass

class DirectoryClient(object):
    def start(self):
        pass
    def shutdown(self):
        pass


import socketserver

class MyTCPHandler(socketserver.BaseRequestHandler):
    def setup(self):
        print("Connection received from %s" % str(self.client_address))
        self.request.sendall("Welcome!\n".encode('utf-8'))
    def handle(self):
        print(self.server.arg)
        while True:
            # self.request is the TCP socket connected to the client
            self.data = self.request.recv(1024).strip()
            self.server.arg.append(self.data.decode('utf-8'))
            if self.data == "q".encode('utf-8'):
                break
            print("{} wrote:".format(self.client_address[0]))
            print(self.data)
            # just send back the same data, but upper-cased
            self.request.sendall(self.data.upper())
    def finish(self):
        self.request.sendall("Goodbye!  Please come back soon.".encode('utf-8'))

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True
    def __init__(self, port, RequestHandlerClass):
        socketserver.TCPServer.__init__(self, ('', port), RequestHandlerClass)
        self.arg = []

if __name__ == "__main__":

    # Create the server, binding to localhost on port 9999
    server = ThreadedTCPServer(9999, MyTCPHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.shutdown()

# vim: expandtab shiftwidth=4 softtabstop=4 textwidth=80:
