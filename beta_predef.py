#!/usr/bin/python2
# -*- coding: utf-8 -*-

nodes =dict()
links =dict()
ip2portTable=dict()

port2hostTable=dict()

statemachine_pos = {}

alltable = dict()

taprulecount = 0

saveflowrules = dict()

oldsaveflowrules = dict()

savetapport = dict()

selectedshortestpath=None
selectedsrcip=None
selecteddstip=None


beta = 0

firstrun = True

portidmap=dict()

