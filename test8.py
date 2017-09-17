#!/usr/bin/python2
# -*- coding: utf-8 -*-

import sys
import re
import eventlet
import time
import Queue
import math

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, set_ev_cls, CONFIG_DISPATCHER
from ryu.ofproto import ofproto_v1_3, ofproto_v1_3_parser
from broccoli import event, Connection,bro_conn_get_fd
from pkg_resources import load_entry_point
from ryu.lib import hub

from eventlet.green import select

import predef8 as predef

app = None

################# Bro ################
@event
def updateinfo(id,flowType,parm1,parm2):
    global app
    print(time.clock())
    print(id,flowType,parm1,parm2)

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


_tapdsts=[(1,4),(3,4),(6,4)]
_count = [0] * len(_tapdsts)

def tcp_tap(inport,outport):

    global _tapdsts,_count

    path = shortestpath(inport,outport,weight=getweight)
    incweight_path(path)
    pathmap = dict(path)
    srcnodes = pathmap.keys()

    tap_path = shortestpath_tap(_tapdsts[0],srcnodes,weight=getweight)
    ci = 0
    for i in range(1,len(_tapdsts)):
        tap_path1 = shortestpath_tap(_tapdsts[i], srcnodes, weight=getweight)
        if _count[i]<_count[ci]:
            tap_path = tap_path1
            ci = i
        elif _count[i]==_count[ci]:
            if len(tap_path1)<len(tap_path):
                tap_path=tap_path1
                ci = i
    incweight_path(tap_path)
    _count[ci]=_count[ci]+1

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
    items = predef.ip2portTable.items()
    for ip1,port1 in items:
        for ip2,port2 in items:
            if ip1!=ip2:
                path = shortestpath(port1,port2,weight=defaultwight)
                incweight_path(path)
                print(port1,port2,path)
                for a,p in path:
                    ipMatch = Match(eth_type=0x0800,ipv4_src=ip1,ipv4_dst=ip2)
                    alltable[a].append((1,ipMatch,[ActionOutput(p)]))
    # tcp + tap
    items = predef.ip2portTable.items()
    for ip1,port1 in items:
        for ip2,port2 in items:
            if ip1!=ip2:
                pathmap = tcp_tap(port1,port2)
                print(port1,port2,pathmap)
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
    port = tuple(port)
    assert len(port)==2
    if _weight.get(port)==None:
        _weight[port]=2
    else:
        _weight[port]=_weight[port]+1

def incweight_path(path):
    for i in path:
        incweight(i)


################# App ################

class TestApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TestApp, self).__init__(*args, **kwargs)
        print('init')
        global app
        app=self
        self.count=0
        self.pretable=pre_generate_flows()
        self.bro_thread = hub.spawn(self._bro_thread)

    def _bro_thread(self):
        while True:
            try:
                self.bc = Connection('127.0.0.1:47758')
                fd = bro_conn_get_fd(self.bc.bc)
                while True:
                    select.select([fd, ], [], [])
                    self.bc.processInput()
                    print('bro process input')
            except Exception,e:
                print(e.message)
            time.sleep(1)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        self.count=self.count+1
        print(self.count)
        msg = ev.msg
        dp = msg.datapath
        flows = self.pretable[dp.id]
        for i in flows:
            self.add_flow(dp,*i)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        print('get pkt')

################# self start ################

if __name__ == '__main__':
    sys.argv.append('test8.py')
    sys.argv.append('--verbose')
    sys.argv.append('--enable-debugger')
    sys.exit(
        load_entry_point('ryu==4.15', 'console_scripts', 'ryu-manager')()
    )
