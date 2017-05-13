# COMP 3331 Assignment 1

By Gabriel Tapuc, z5150268, May 12 2017

## Introduction

Using python 2.7

## Design

Each router communicates with its neighbours via UDP using the following syntax:

Command	| Description
-------	| -----------
H \<node> beat	| Heartbeat message. \<node> is the node ID of the sender.
DV \<node> \<destNode1> \<cost\_to\_destNode1> \<destNode2> \<cost\_to\_destNode2> ...	| Distance vector from node \<node>. Following is a series of the nodes where \<node> can go and with what cost to that particular node.