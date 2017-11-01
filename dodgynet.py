#!/usr/bin/env python3
import sys
import os
import math
import Puncher
import signal
from UdpTrackerServer import *
from UdpTrackerClient import *
import Puncher
import endpoint

CHUNK_SIZE = 1024
DEFAULT_PORT = 60760
DEFAULT_IP = "127.0.0.1"
DEFAULT_PUNCHER_A = (DEFAULT_IP, 50818)

def help():
    print ("Usage:")
    print ("p2pclient seed upload/join <filename>")
    print ("p2pclient leech list")
    #print ("p2pclient leech query <filename>")
    print ("p2pclient leech download <filename>")

def main():
    
    if len(sys.argv) < 3:
        help()
        return

    clientType = sys.argv[1]
    option = sys.argv[2]

    if (clientType == "seed"):

        fileName = sys.argv[3]
        #TODO change to puncher addr
        ep = endpoint.DummyEndpoint(DEFAULT_PUNCHER_A)
        ep.file_to_mem(fileName)
        print("[Seeder] File Chunk Indices = %s" % str(ep.total_chunks))
        print("[Seeder] File byte size = %d" % ep.file_size)

        if (option == "upload"):
            dirClient = Puncher.DirectoryClient()
            dirClient.new_file(fileName, ep.total_chunks)
        
        # become seeder
        client = UdpTrackerClient(DEFAULT_IP, DEFAULT_PORT) #TODO change to file dir IP
        client.join()
        print (client.listen_for_response())

        chunk_have = NO_CHUNK
        for c in ep.total_chunks:
            client.announce(NO_CHUNK, c)
        
        #init weakling protocol
        #get server inside
        #do wait loop until user terminates
        #tTODO
        c = []
        ep.start()

        # Wait until User terminates
        u_input = None
        while u_input!='Quit':
                u_input = input("Type Quit to stop seeding and quit the program:")

        print("Quitting!")

    elif (clientType == "leech" and option == "list"):
        # call dir client list, display results and quit
        dirClient = Puncher.DirectoryClient()
        listFiles = dirClient.list()

        for element in listFiles:
            print (element)


    elif (clientType == "leech" and option == "download"):
        fileName = sys.argv[3]
        portNum = DEFAULT_PORT

        client = UdpTrackerClient(DEFAULT_IP, portNum) #TODO change to file directory ip
        client.join()
        #print (client.listen_for_response())
        resp = client.listen_for_response()
        #print ('Connection: '+ resp['response']['completed'])
        total_chunks = resp['response']['chunk_list']

        ep = endpoint.DummyEndpoint(DEFAULT_PUNCHER_A, client) #TODO change to puncher addr
        ep.init_mem(fileName, 48, total_chunks)
        ep.start()
        ep.get_input()
        
        print(client.shutdown()) # exit after completing file download

    else:
        print("upload/join/list/query/download")
        print ("Usage:")
        print ("p2pclient seed upload/join <filename>")
        print ("p2p seed list")
        print ("p2pclient leech list")
        print ("p2pclient leech query <filename>")
        print ("p2pclient leech download <filename>")

if __name__ == "__main__":
    main()
