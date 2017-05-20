# COMP 3331 Assignment 1

By Gabriel Tapuc, z5150268, May 12 2017

## Introduction

Using **python 2.7**. In this assignment, the basic and poison reverse functionalities are implemented.

## Design

Each router communicates with its neighbours via UDP using the following syntax:

Command	| Description
-------	| -----------
H \<node> beat	| Heartbeat message. \<node> is the node ID of the sender.
DV \<node> \<destNode1> \<cost\_to\_destNode1> \<destNode2> \<cost\_to\_destNode2> ...	| Distance vector from node \<node>. Following is a series of the nodes where \<node> can go and with what cost to that particular node.

Throughout the execution of the program, references to the node's direct neighbours, known nodes and a dictionary containing the distance vectors are kept.

From a high level view, each node sends a *heartbeat* message to its neighbours every second to indicate that it is alive, and each node keeps track of these heartbeats. If a node does not receive **10** heartbeatSTA, then it assumes that the respective node is offline. I chose the number 10 and not a smaller one because during development, I needed some time to start the nodes, and if this number was too low and I would take too much time to start a node, the nodes that were already started would consider that particular node offline, which wasn't the case.

Every 3 seconds, a distance vector will be sent to the adjacent nodes, and depending of presence of the *-p* flag, the poison reverse module will be employed or not.

The program first starts by parsing the command line arguments, then loading the config file into the global variables. Next, a series of threads are dispatched: one thread needs to listen for incoming messages, one needs to send heartbeats, one needs to check for offline nodes, one needs to periodically send the distance vectors and a last one needs to check for stabilization.

To check if the distance vectors have stabilized, the following method is employed. First, a global variables `STABILIZATION_TIME = 10` and `STABILIZATION_CHECK_INTERVAL = 1` are set. Then, a thread is dispatched, checking for stabilization every (`STABILIZATION_CHECK_INTERVAL`) second. It is important to note, that at every point in time, we keep track of a dictionary of distance vectors, a time when it was last changed and its hash. Every time there's a potential change, a function is ran that computes a new hash of the string representation of the dictionary and compares it with the existing hash. If the values are different, then it means that the distance vectors have been changed and its hash and last time changed variables must be updated.

## Borrowed code

As a foundation, I started my program with the UDP example provided from the class' material.

