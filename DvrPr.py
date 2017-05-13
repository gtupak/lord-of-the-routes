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


art = \
" ___________________        ____....-----....____\n\
(__Node %s started__)   ==============================\n\
    ______\\   \\_______.--'.  `---..._____...---'\n\
    `-------..__            ` ,/\n\
                `-._ -  -  - |\n\
                    `-------'"

'''
Dictionary to store the neighbors of this node and their properties.
{   
    'B': {'weight': 21, 'port': 2001},
    ...
}
'''
neighbours = {}

# List of nodes discovered so far
discoveredNodes = []

'''
Dictionary holding the distance vectors table. 
{
    <to_node>: {<via_node1>: <cost2>, <via_node2>: <cost2>},
    'B': {'B': 5, 'C': 7, 'D': 10},
    ...
}
'''
distance_vectors = {}


def send_msg_to_node(nID, msg):
    nPort = neighbours[nID]['port']
    nSocket = socket(AF_INET, SOCK_DGRAM)
    nSocket.sendto(msg, (SERVER_NAME, nPort))
    nSocket.close()


def broadcast_to_neighbours(msg):
    for nID in neighbours:
        send_msg_to_node(nID, msg)


def initialize_dv():
    print 'Initializing distance vectors.'
    for to_nID in discoveredNodes:
        distance_vectors[to_nID] = {}
        for via_nID in discoveredNodes:
            distance_vectors[to_nID][via_nID] = float('inf')

    for nID in neighbours:
        distance_vectors[nID][nID] = neighbours[nID]['weight']


def print_shortest_path():
    for nID in discoveredNodes:
        msg = 'shortest path to node %s:' % nID
        nextHop = ''
        cost = float('inf')
        for via_nID in distance_vectors[nID]:
            viaCost = distance_vectors[nID][via_nID]
            if viaCost < cost:
                nextHop = via_nID
                cost = viaCost
        print '%s the next hop is %s and the cost is %d' % (msg, nextHop, cost)


def send_DV():
    threading.Timer(DV_UPDATE_TIME, send_DV).start()
    vectorToSend = {}
    msg = 'DV %s' % NODE_ID

    for to_nID in distance_vectors:
        minWeight = float('inf')
        viaWeights = distance_vectors[to_nID]

        for via_nID in viaWeights:
            minWeight = min(minWeight, viaWeights[via_nID])

        vectorToSend[to_nID] = minWeight

    # craft msg
    for to_nID in vectorToSend:
        msg += ' %s %d' % (to_nID, vectorToSend[to_nID])

    # broadcast new DV
    broadcast_to_neighbours(msg)

    print 'DV sent: ' + msg


def updateDV(from_nID, newDistVector):
    costToVia_fromNode = distance_vectors[from_nID][from_nID] # cost to fromNode via fromNode
    for to_nID in newDistVector:
        if to_nID == NODE_ID:
            continue

        if to_nID not in distance_vectors:              # toNode not yet discovered; initialize weights
            distance_vectors[to_nID] = {}
            discoveredNodes.append(to_nID)

            for via_nID in discoveredNodes:
                distance_vectors[to_nID][via_nID] = float('inf')

        toCost = newDistVector[to_nID]                  # cost of from_nID to to_nID
        myToCost = distance_vectors[to_nID][from_nID]   # cost current node to

        distance_vectors[to_nID][from_nID] = min(myToCost, toCost + costToVia_fromNode)

    print '>>> DV updated!'
    print_shortest_path()


def heartbeat():
    threading.Timer(HEARTBEAT_TIME, heartbeat).start()
    for nID in neighbours:
        msg = 'H %s beat' % NODE_ID
        send_msg_to_node(nID, msg)


def listen_incoming_messages():
    nListener = socket(AF_INET, SOCK_DGRAM)
    nListener.bind(('', NODE_PORT))
    print 'Listener initialized.'
    while 1:
        msg, _ = nListener.recvfrom(2048)
        msgType = msg.split()[0]
        if msgType == 'H':
            continue #TODO
        elif msgType == 'DV':
            dv = {}
            msg = msg.split()
            nFrom = msg[1]
            i = 2
            while i < len(msg):
                to_nID = msg[i]
                costTo_nID = int(msg[i+1])
                dv[to_nID] = costTo_nID
                i += 2
            updateDV(nFrom, dv)


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
            neighbourID = line[0]
            neighbourWeight = int(line[1])
            neighbourPort = int(line[2])
            neighbour = {'weight': neighbourWeight, 'port': neighbourPort}
            neighbours[neighbourID] = neighbour

            discoveredNodes.append(neighbourID)

        NODE_WEIGHT = int(config_file_lines[0])

        # Other configurations
        HEARTBEAT_TIME = 1  # heartbeat every second
        DV_UPDATE_TIME = 5  # send DV update every 5 seconds
        SERVER_NAME = 'localhost'

        print art % NODE_ID
        initialize_dv()

        listener_thread = threading.Thread(target=listen_incoming_messages)
        listener_thread.start()

        heartbeat() # start heartbeat
        send_DV() # start distance vector broadcasting
