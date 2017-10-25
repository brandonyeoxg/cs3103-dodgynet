import sys
import Puncher
import signal

def main():
    try:
        master = (sys.argv[1], int(sys.argv[2]))
    except (IndexError, ValueError):
        print >>sys.stderr, "usage: %s <host> <port> <pool>" % sys.argv[0]
        sys.exit(65)
    ep = None

    try:
        ep = Puncher.DummyEndpoint(master)
        ep.start()
        def handler(signal, frame):
            ep.shutdown()
            exit()
        signal.signal(signal.SIGINT, handler)
        ep.get_input()
    except (KeyboardInterrupt, SystemExit):
        print("Caught, Shutting down from main")
        ep.shutdown()
        exit()
    print("Exit!!")

if __name__ == "__main__":
    main()
