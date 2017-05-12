# Using python2.7

# noinspection PyByteLiteral
'''
cmd line args:

NODE_ID, 
the ID for this node (i.e. router). This argument must be a single uppercase alphabet (e.g.: A, B, etc.).

NODE_PORT, 
the port number on which this node will send and receive packets from its neighbours.

CONFIG.TXT, 
this file will contain the costs to the neighbouring nodes. 
It will also contain the port number on which each neighbour is waiting for routing packets. 
An example of this file is provided below:
2           nr of neighbors
B 5 2001    <neighbor ID> <cost to reach this neighbor> <port of the neighbor>
C 7 2002

POISONED REVERSE FLAG (-p), 
this is an optional argument, which is used to turn on/off Poisoned reverse. 
This means that your program should accept either 3 or 4 arguments. 
If the -p flag is present in the argument list then poisoned reverse should be employed in the routing protocol. 
If this flag is absent then only basic distance vector should be used.

to run: 
python DvrPr.py A 2000 config.txt -p

Eventually print final routing table. ex:

Shortest path to node B: the next hop is D and the cost is 10
Shortest path to node C: the next hop is B and the cost is 11.5
'''

import sys
from socket import *
import threading

'''
Dictionary to store the neighbors and their properties.
{   
    'A': {'cost': 21, 'port': 2001},
    ...
}
'''
neighbours = {}

def heartbeat():
    threading.Timer(HEARTBEAT_TIME, heartbeat).start()
    for nID in neighbours:
        nPort = neighbours[nID]['port']
        nSocket = socket(AF_INET, SOCK_DGRAM)
        heartbeatMsg = '%s beat' % NODE_ID
        nSocket.sendto(heartbeatMsg, (SERVER_NAME, nPort))
        nSocket.close()

def listen_incoming_messages():
    nListener = socket(AF_INET, SOCK_DGRAM)
    nListener.bind(('', NODE_PORT))
    print '%s: Listener initialized.' % NODE_ID
    while 1:
        msg, _ = nListener.recvfrom(2048)
        print msg

if __name__ == '__main__':
    cmdArgs = sys.argv
    if len(cmdArgs) < 4:
        print 'Usage: python DvrPr.py <node ID> <port> <config.txt> [-p]'
    else:
        NODE_ID = cmdArgs[1]
        NODE_PORT = int(cmdArgs[2])
        CONFIG_TXT_PATH = cmdArgs[3]
        POISON_REVERSE_ENABLED = False
        if '-p' in cmdArgs:
            POISON_REVERSE_ENABLED = True

        # Parse config file
        config_file = open(CONFIG_TXT_PATH, 'r')
        config_file_lines = config_file.readlines()
        config_file_lines = [line.translate(None, '\n') for line in config_file_lines] # remove \n chars from lines

        for i in range(1, len(config_file_lines)):
            line = config_file_lines[i]
            line = line.split()
            neighbourId = line[0]
            neighbourWeight = int(line[1])
            neighbourPort = int(line[2])
            neighbour = {'weight': neighbourWeight, 'port': neighbourPort}
            neighbours[neighbourId] = neighbour

        NODE_WEIGHT = int(config_file_lines[0])

        # Other configurations
        HEARTBEAT_TIME = 1  # heartbeat every second
        DV_UPDATE_TIME = 5  # send DV update every 5 seconds
        SERVER_NAME = 'localhost'

        heartbeat()
        listener_thread = threading.Thread(target=listen_incoming_messages)
        listener_thread.start()
