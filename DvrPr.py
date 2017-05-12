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
If the – p flag is present in the argument list then poisoned reverse should be employed in the routing protocol. 
If this flag is absent then only basic distance vector should be used.

to run: 
python Dvr A 2000 config.txt -p

Eventually print final routing table. ex:

Shortest path to node B: the next hop is D and the cost is 10
Shortest path to node C: the next hop is B and the cost is 11.5
'''


if __name__ == '__main__':
    print 'ohaio gozaimas'