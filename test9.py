#!/usr/bin/python2
# -*- coding: utf-8 -*-

import sys
import re
import time
import Queue
import math
import networkx as nx
import random

from matplotlib import pyplot as plt

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, set_ev_cls, CONFIG_DISPATCHER
from ryu.ofproto import ofproto_v1_3, ofproto_v1_3_parser
from broccoli import event, Connection,bro_conn_get_fd
from pkg_resources import load_entry_point
from ryu.lib import hub

import predef

global statemachine_pos,alltable,taprulecount

################# pre route ################

def arpspt():
    nodes = predef.nodes
    links = predef.links
    flags = dict.fromkeys(nodes.keys(),False)
    nodeidlist = nodes.keys()
    outports = []
    while len(nodeidlist)>0:
        lastid = nodeidlist.pop()
        if not flags[lastid]: #broadcast from lastid
            q = Queue.Queue()
            q.put(lastid)
            flags[lastid] = True
            while not q.empty():
                a = q.get()
                for portid in nodes[a]:
                    port = (a,portid)
                    peerport = links.get(port)
                    if peerport==None:
                        if predef.port2hostTable.has_key(port):
                            outports.append(port)
                    elif not flags[peerport[0]]:
                        outports.append(port)
                        outports.append(peerport)
                        q.put(peerport[0])
                        flags[peerport[0]]=True
    ret={}
    for a,p in outports:
        p1 = ret.get(a)
        if p1 == None:
            ret[a]=[p,]
        else:
            p1.append(p)
    return ret

_linkpeerport_to_node ={}

def getlinkpeerport_to_node(n):
    global _linkpeerport_to_node
    ll = _linkpeerport_to_node.get(n)
    if ll!=None:
        return ll
    ports = predef.nodes[n]
    links = predef.links
    ll = []
    for p in ports:
        pp = links.get((n,p))
        if pp!=None:
            assert links[pp]==(n,p)
            ll.append(pp)
    _linkpeerport_to_node[n]=ll
    return ll


def defaultwight(outport):
    assert predef.links.has_key(outport)
    return 1

def shortestpath(inport,outport,weight=defaultwight):
    nodes = predef.nodes
    links = predef.links
    innode = inport[0]
    outnode = outport[0]
    if innode == outnode:
        return [outport]
    dis = dict.fromkeys(nodes.keys(),-1)
    dis[innode]=0
    flags = dict.fromkeys(nodes.keys(),False)
    flags[innode] = True
    selectednode = innode
    pathlinks = {}
    while True:
        for port in nodes[selectednode]:
            aport = (selectednode,port)
            p2 = links.get(aport)
            if p2!=None:
                n2 = p2[0]
                if not flags[n2]:
                    dis_new = dis[selectednode] + weight(aport)
                    if dis[n2]==-1 or dis[n2]> dis_new:
                        dis[n2]=dis_new
                        pathlinks[n2] = aport
        selectednode = None
        mindis = -1
        for node in nodes:
            if not flags[node]:
                if dis[node]!=-1 and (mindis==-1 or dis[node]<mindis):
                    mindis = dis[node]
                    selectednode = node
        if selectednode == None:
            break
        flags[selectednode] = True
        if selectednode == outnode:
            break
    if pathlinks.get(outnode) == None:
        return []
    ret = [outport]
    last = outnode
    while last!=innode:
        ap = pathlinks[last]
        ret.append(ap)
        last = ap[0]
    ret.reverse()
    return ret



def shortestpath_tap(dstport,srcnodes,weight=defaultwight):
    assert isinstance(srcnodes,list)
    nodes = predef.nodes
    links = predef.links
    outnode = dstport[0]
    if outnode in srcnodes:
        return [dstport]
    dis = dict.fromkeys(nodes.keys(),-1)
    dis[outnode]=0
    flags = dict.fromkeys(nodes.keys(),False)
    flags[outnode] = True
    selectednode = outnode
    pathlinks = {}
    while True:
        for port in nodes[selectednode]:
            aport = (selectednode,port)
            p2 = links.get(aport)
            if p2!=None:
                n2 = p2[0]
                if not flags[n2]:
                    dis_new = dis[selectednode] + weight(p2)
                    if dis[n2]==-1 or dis[n2]> dis_new:
                        dis[n2]=dis_new
                        pathlinks[n2] = p2
        selectednode = None
        mindis = -1
        for node in nodes:
            if not flags[node]:
                if dis[node] != -1 and (mindis == -1 or dis[node] < mindis):
                    mindis = dis[node]
                    selectednode = node
        if selectednode == None:
            break
        flags[selectednode] = True
        if selectednode in srcnodes:
            break
    if selectednode == None:
        return []
    ret = []
    last = selectednode
    while last!=outnode:
        ap = pathlinks[last]
        ret.append(ap)
        last = links[ap][0]
    ret.append(dstport)
    return ret


def dummy_weight(port):
    pp =  predef.links.get(port)
    assert pp!=None
    return pp[0]*port[1]+pp[1]*port[0]

def tcp_tap(inport,outport):

    global statemachine_pos
    path = shortestpath(inport,outport,weight=getweight)
    incweight_path(path)
    pathmap = dict(path)

    tap_path=None
    for tapdst in statemachine_pos:
        ret = shortestpath_tap((tapdst,'tap'),pathmap.keys())
        if tap_path==None:
            tap_path=ret
        elif len(ret)<len(tap_path):
            tap_path=ret
    incweight_path(tap_path)

    global  taprulecount
    taprulecount=taprulecount+len(tap_path)-1

    tapport = tap_path[0]
    tapnode = tapport[0]
    pathmap[tapnode]=(pathmap[tapnode],tapport[1])
    for n,p in tap_path[1:]:
        assert not pathmap.has_key(n)
        pathmap[n]=p
    return pathmap





def pre_generate_flows():
    of = ofproto_v1_3
    ofp = ofproto_v1_3_parser
    Match = ofp.OFPMatch
    ActionOutput = ofp.OFPActionOutput
    alltable = dict.fromkeys(predef.nodes.keys(),None)
    # default table-miss
    emptymatch = Match()
    puntactions = [ActionOutput(of.OFPP_CONTROLLER,of.OFPCML_NO_BUFFER)]
    for a in alltable:
        alltable[a]=[(0,emptymatch,puntactions)]
    # arp broadcast
    arpMatch = Match(eth_type=0x0806)
    arppath = arpspt()
    for a,ports in arppath.items():
        outputs = [ActionOutput(x) for x in ports]
        alltable[a].append((1,arpMatch,outputs))
    # ip shortest path
    # items = predef.ip2portTable.items()
    # for ip1,port1 in items:
    #     for ip2,port2 in items:
    #         if ip1!=ip2:
    #             path = shortestpath(port1,port2,weight=defaultwight)
    #             incweight_path(path)
    #             for a,p in path:
    #                 ipMatch = Match(eth_type=0x0800,ipv4_src=ip1,ipv4_dst=ip2)
    #                 alltable[a].append((1,ipMatch,[ActionOutput(p)]))
    # tcp + tap
    items = predef.ip2portTable.items()
    for ip1,port1 in items:
        for ip2,port2 in items:
            if ip1!=ip2:
                pathmap = tcp_tap(port1,port2)
                for a in pathmap:
                    ipMatch = Match(eth_type=0x0800,ipv4_src=ip1,ipv4_dst=ip2,ip_proto=6)
                    if isinstance(pathmap[a],tuple):
                        alltable[a].append((2,ipMatch,[ActionOutput(p) for p in pathmap[a]]))
                    else:
                        alltable[a].append((2, ipMatch, [ActionOutput(pathmap[a])]))
    return alltable


################# inc weight ##############


_weight = {}

def getweight(port):
    global _weight
    if _weight.get(port)==None:
        return 1
    else:
        return _weight[port]

def incweight(port):
    global _weight
    if _weight.get(port)==None:
        _weight[port]=2
    else:
        _weight[port]=_weight[port]+1

def incweight_path(path):
    for i in path:
        incweight(i)



if __name__=="__main__":
    predef.nodes={}
    predef.links={}
    predef.ip2portTable={}
    nodes=predef.nodes
    links=predef.links
    ip2portTable=predef.ip2portTable
    topology_name = "Noel"
    filename = "/home/yutao/Desktop/networkmap-evaluation/rsa-eval/dataset/topologyzoo/sources/" + topology_name + ".graphml"
    topo = nx.read_graphml(filename).to_undirected()

    # labels={}
    # for n in topo.adj:
    #     labels[n]=n
    # pos = nx.spring_layout(topo)
    # nx.draw(topo,pos=pos)
    # nx.draw_networkx_labels(topo,pos,labels=labels)
    # plt.show()

    statemachine_pos= {'n0'}

    for n in topo.adj:
        predef.nodes[n]=[]

    for s in statemachine_pos:
        predef.nodes[s].append('tap')

    for n in topo.adj:
        for pn in topo.adj[n]:
            eid=topo.adj[n][pn]['id']
            predef.nodes[n].append(eid)
            predef.links[(n,eid)]=(pn,eid)

    keys = nodes.keys()
    for i in range(2*len(nodes)):
        hosti = "192.168.0.%d"%i
        hostisw = keys[random.randint(0,len(keys)-1)]
        nodes[hostisw].append(hosti)
        ip2portTable[hosti]=(hostisw,hosti)
    for n in predef.nodes:
        predef.nodes[n] = tuple(predef.nodes[n])
    print(predef.nodes)
    print(predef.links)
    print(ip2portTable)


    global taprulecount
    taprulecount=0
    alltable = pre_generate_flows()
    #print(alltable)

    count=0
    for k in alltable.values():
        count=count+len(k)

    print("(%d,%d,)"%(count,taprulecount))
    print(len(nodes))
