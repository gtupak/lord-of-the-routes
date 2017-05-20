# Using python2.7

import sys
from socket import *
import threading
import datetime as dateTime
import time

art = \
" ___________________        ____....-----....____\n\
(__Node %s started__)   ==============================\n\
    ______\\   \\_______.--'.  `---..._____...---'\n\
    `-------..__            ` ,/\n\
                `-._ -  -  - |\n\
                    `-------'"

'''
Dictionary to store the neighbors of this node and their properties.
The key 'changeWeight' exists only if poisoned reverse is enabled.
{   
    'B': {'weight': 21, 'port': 2001, 'changeWeight': 50, 'lastHeartbeat': <timeObject>},
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

# Hash of distance vectors dict to allow difference checking
dv_hash = 0
# time since last distance vectors dict change
dv_timeLastChanged = dateTime.datetime.now()

# True if DV has stabilized
stabilized = False

# True if weights have already been changed
weights_changed = False

# List of nodes that have changed weights and their remaining checks.
nodes_increased_weight = []


def send_msg_to_node(node, msg):
    nPort = neighbours[node]['port']
    nSocket = socket(AF_INET, SOCK_DGRAM)
    nSocket.sendto(msg, (SERVER_NAME, nPort))
    nSocket.close()


# Updates the DV when one node is detected to be offline
def update_dv_offline_node(offline_node):
    for to_nID in distance_vectors:
        for via_nID in distance_vectors[to_nID]:
            if to_nID == offline_node:
                distance_vectors[to_nID][via_nID] = WEIGHT_OFFLINE
            elif via_nID == offline_node:
                distance_vectors[to_nID][via_nID] = WEIGHT_OFFLINE


def check_update_dv_hash():
    global dv_hash, dv_timeLastChanged, stabilized
    dv_newHash = hash(repr(distance_vectors))
    if dv_hash != dv_newHash:
        dv_hash = dv_newHash
        dv_timeLastChanged = dateTime.datetime.now()
        print '>>> DV updated!'
        stabilized = False


def broadcast_to_neighbours(msg):
    for nID in neighbours.keys():
        send_msg_to_node(nID, msg)


def heartbeat():
    thread = threading.Timer(HEARTBEAT_TIME, heartbeat)
    thread.daemon = True
    thread.start()
    msg = 'H %s beat' % NODE_ID
    broadcast_to_neighbours(msg)


def heartbeat_listener():
    while True:
        for nID in neighbours.keys():
            lastBeat = neighbours[nID]['lastHeartbeat']
            elapsedTime = dateTime.datetime.now() - lastBeat
            # Consider a node offline if we haven't received 10 heartbeats
            if elapsedTime.seconds > HEARTBEAT_TIME * 10:
                # Update dv since node is dead
                print '>>> Node %s is offline!' % nID
                update_dv_offline_node(nID)

                # Remove node from neighbors list
                del neighbours[nID]

        check_update_dv_hash()


def initialize_dv():
    global dv_hash, dv_timeLastChanged
    # print 'Initializing distance vectors.'
    for to_nID in discoveredNodes:
        distance_vectors[to_nID] = {}
        for via_nID in discoveredNodes:
            distance_vectors[to_nID][via_nID] = WEIGHT_UNKNOWN

    for nID in neighbours:
        distance_vectors[nID][nID] = neighbours[nID]['weight']

    dv_hash = hash(repr(distance_vectors))
    dv_timeLastChanged = dateTime.datetime.now()


# Returns the via node to go to to_node and the weight
def get_via_node(to_node):
    optimalNode = ''
    minWeight = WEIGHT_OFFLINE
    for viaNode in distance_vectors[to_node]:
        viaWeight = distance_vectors[to_node][viaNode]
        if viaWeight != WEIGHT_POISON and viaWeight != WEIGHT_OFFLINE and viaWeight != WEIGHT_UNKNOWN:
            if viaWeight < minWeight:
                minWeight = viaWeight
                optimalNode = viaNode
    return optimalNode, minWeight


def print_shortest_path():
    for to_nID in distance_vectors:
        msg = 'shortest path to node %s:' % to_nID
        nextHop, cost = get_via_node(to_nID)
        if cost != WEIGHT_OFFLINE:
            print '%s the next hop is %s and the cost is %.1f' % (msg, nextHop, cost)


def send_dv():
    thread = threading.Timer(DV_UPDATE_TIME, send_dv)
    thread.daemon = True
    thread.start()
    vectorToSend = {}
    minToViaDict = {}

    for to_nID in distance_vectors:
        minToVia, minWeight = get_via_node(to_nID)
        minToViaDict[to_nID] = minToVia

        vectorToSend[to_nID] = minWeight

    # craft msg & broadcast to neighbours
    for nID in neighbours.keys():
        msg = 'DV %s' % NODE_ID
        for to_nID in vectorToSend:
            if to_nID == nID:
                continue
            elif minToViaDict[to_nID] == nID and POISON_REVERSE_ENABLED:
                msg += ' %s %.1f' % (to_nID, WEIGHT_POISON)
            else:
                msg += ' %s %.1f' % (to_nID, vectorToSend[to_nID])
        send_msg_to_node(nID, msg)


def update_dv(from_node, new_dist_vector):
    global dv_hash, dv_timeLastChanged, stabilized

    costToVia_fromNode = distance_vectors[from_node][from_node]  # cost to fromNode via fromNode
    for to_nID in new_dist_vector:
        if to_nID == NODE_ID:
            continue

        if to_nID not in distance_vectors:              # toNode not yet discovered; initialize weights
            distance_vectors[to_nID] = {}
            discoveredNodes.append(to_nID)

            for via_nID in discoveredNodes:
                distance_vectors[to_nID][via_nID] = WEIGHT_UNKNOWN

        toCost = new_dist_vector[to_nID]                  # cost of from_nID to to_nID
        myToCost = distance_vectors[to_nID][from_node]   # cost current node to

        if myToCost == WEIGHT_UNKNOWN:
            distance_vectors[to_nID][from_node] = costToVia_fromNode + toCost
        elif myToCost == WEIGHT_OFFLINE:
            continue
        elif toCost == WEIGHT_OFFLINE:
            update_dv_offline_node(to_nID)
        elif toCost == WEIGHT_POISON:
            distance_vectors[to_nID][from_node] = WEIGHT_POISON
        else:
            distance_vectors[to_nID][from_node] = toCost + costToVia_fromNode

    check_update_dv_hash()


def listen_incoming_messages():
    nListener = socket(AF_INET, SOCK_DGRAM)
    nListener.bind(('', NODE_PORT))
    print 'Node is ready to receive incoming messages...'
    while True:
        msg, _ = nListener.recvfrom(2048)
        msg = msg.split()
        msgType = msg[0]
        if msgType == 'H':
            fromBeat = msg[1]
            timeNow = dateTime.datetime.now()
            neighbours[fromBeat]['lastHeartbeat'] = timeNow

        elif msgType == 'DV':
            dv = {}
            nFrom = msg[1]
            j = 2
            while j < len(msg):
                to_nID = msg[j]
                costTo_nID = float(msg[j+1])
                dv[to_nID] = costTo_nID
                j += 2

            update_dv(nFrom, dv)


def check_stabilization():
    global stabilized, weights_changed
    thread = threading.Timer(STABILIZATION_CHECK_INTERVAL, check_stabilization)
    thread.daemon = True
    thread.start()
    timeNow = dateTime.datetime.now()
    timeElapsed = timeNow - dv_timeLastChanged
    if timeElapsed.seconds > STABILIZATION_TIME:
        if not stabilized:
            if POISON_REVERSE_ENABLED and not weights_changed:
                print 'Stabilized!'
                print_shortest_path()

                print 'Changing weights...'
                for neighbour in neighbours.keys():
                    changeWeight = neighbours[neighbour]['changeWeight']
                    currWeight = distance_vectors[neighbour][neighbour]
                    if currWeight != changeWeight:
                        nodes_increased_weight.append(neighbour)
                        distance_vectors[neighbour][neighbour] = changeWeight
                check_update_dv_hash()
                weights_changed = True
            else:
                print '>>> Distance vectors stabilized!'
                print_shortest_path()
                stabilized = True
    else:
        remaining = STABILIZATION_TIME - timeElapsed.seconds
        if remaining % 5 == 0:
            print '%d seconds until stabilization...' % remaining


def parse_config():
    config_file = open(CONFIG_TXT_PATH, 'r')
    config_file_lines = config_file.readlines()
    config_file_lines = [line.translate(None, '\n') for line in config_file_lines]  # remove \n chars from lines

    now = dateTime.datetime.now()
    for i in range(1, len(config_file_lines)):
        cfgLine = config_file_lines[i]
        cfgLine = cfgLine.split()
        neighbourChangeWeight = None
        neighbourID = cfgLine[0]
        neighbourWeight = float(cfgLine[1])

        if POISON_REVERSE_ENABLED:
            neighbourChangeWeight = float(cfgLine[2])
            neighbourPort = int(cfgLine[3])
        else:
            neighbourPort = int(cfgLine[2])

        neighbour = {'weight': neighbourWeight, 'port': neighbourPort, 'lastHeartbeat': now}
        if POISON_REVERSE_ENABLED:
            neighbour['changeWeight'] = neighbourChangeWeight

        neighbours[neighbourID] = neighbour
        discoveredNodes.append(neighbourID)


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
        parse_config()

        # Other configurations
        HEARTBEAT_TIME = 1          # heartbeat every second
        DV_UPDATE_TIME = 3          # send DV update every 3 seconds
        STABILIZATION_CHECK_INTERVAL = 1    # check if DV has stabilized every second
        STABILIZATION_TIME = 10     # if DV table didn't change after 20s, then assume stabilization
        WEIGHT_UNKNOWN = -1.0       # code for an unknown weight
        WEIGHT_OFFLINE = float('inf')   # code for an offline node
        WEIGHT_POISON = -2.0    # code when a weight has increased
        SERVER_NAME = 'localhost'

        print art % NODE_ID
        initialize_dv()

        # Start listening for messages
        listenThread = threading.Thread(target=listen_incoming_messages)
        listenThread.daemon = True
        listenThread.start()

        # Start heartbeat transmitter and listener
        heartbeat()
        heartThread = threading.Thread(target=heartbeat_listener)
        heartThread.daemon = True
        heartThread.start()

        # Start distance vector broadcasting
        send_dv()

        # start check for stabilization thread
        check_stabilization()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print 'Node %s is shut down.' % NODE_ID
