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