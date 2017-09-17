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
from broccoli import event, Connection, bro_conn_get_fd
from pkg_resources import load_entry_point
from ryu.lib import hub

import beta_predef as predef


################# pre route ################

def arpspt():
    nodes = predef.nodes
    links = predef.links
    flags = dict.fromkeys(nodes.keys(), False)
    nodeidlist = nodes.keys()
    outports = []
    while len(nodeidlist) > 0:
        lastid = nodeidlist.pop()
        if not flags[lastid]:  # broadcast from lastid
            q = Queue.Queue()
            q.put(lastid)
            flags[lastid] = True
            while not q.empty():
                a = q.get()
                for portid in nodes[a]:
                    port = (a, portid)
                    peerport = links.get(port)
                    if peerport == None:
                        if predef.port2hostTable.has_key(port):
                            outports.append(port)
                    elif not flags[peerport[0]]:
                        outports.append(port)
                        outports.append(peerport)
                        q.put(peerport[0])
                        flags[peerport[0]] = True
    ret = {}
    for a, p in outports:
        p1 = ret.get(a)
        if p1 == None:
            ret[a] = [p, ]
        else:
            p1.append(p)
    return ret


#################

_linkpeerport_to_node = {}


def getlinkpeerport_to_node(n):
    global _linkpeerport_to_node
    ll = _linkpeerport_to_node.get(n)
    if ll != None:
        return ll
    ports = predef.nodes[n]
    links = predef.links
    ll = []
    for p in ports:
        pp = links.get((n, p))
        if pp != None:
            assert links[pp] == (n, p)
            ll.append(pp)
    _linkpeerport_to_node[n] = ll
    return ll

#################

def defaultwight(outport):
    assert predef.links.has_key(outport)
    return 1


def shortestpath(inport, outport, weight=defaultwight):
    nodes = predef.nodes
    links = predef.links
    innode = inport[0]
    outnode = outport[0]
    if innode == outnode:
        return [outport]
    dis = dict.fromkeys(nodes.keys(), -1)
    dis[innode] = 0
    flags = dict.fromkeys(nodes.keys(), False)
    flags[innode] = True
    selectednode = innode
    pathlinks = {}
    while True:
        for port in nodes[selectednode]:
            aport = (selectednode, port)
            p2 = links.get(aport)
            if p2 != None:
                n2 = p2[0]
                if not flags[n2]:
                    dis_new = dis[selectednode] + weight(aport)
                    if dis[n2] == -1 or dis[n2] > dis_new:
                        dis[n2] = dis_new
                        pathlinks[n2] = aport
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
        if selectednode == outnode:
            break
    if pathlinks.get(outnode) == None:
        return []
    ret = [outport]
    last = outnode
    while last != innode:
        ap = pathlinks[last]
        ret.append(ap)
        last = ap[0]
    ret.reverse()
    return ret

#
# def shortestpath_tap(dstport, srcnodes, weight=defaultwight):
#     assert isinstance(srcnodes, list)
#     nodes = predef.nodes
#     links = predef.links
#     outnode = dstport[0]
#     if outnode in srcnodes:
#         return [dstport]
#     dis = dict.fromkeys(nodes.keys(), -1)
#     dis[outnode] = 0
#     flags = dict.fromkeys(nodes.keys(), False)
#     flags[outnode] = True
#     selectednode = outnode
#     pathlinks = {}
#     while True:
#         for port in nodes[selectednode]:
#             aport = (selectednode, port)
#             p2 = links.get(aport)
#             if p2 != None:
#                 n2 = p2[0]
#                 if not flags[n2]:
#                     dis_new = dis[selectednode] + weight(p2)
#                     if dis[n2] == -1 or dis[n2] > dis_new:
#                         dis[n2] = dis_new
#                         pathlinks[n2] = p2
#         selectednode = None
#         mindis = -1
#         for node in nodes:
#             if not flags[node]:
#                 if dis[node] != -1 and (mindis == -1 or dis[node] < mindis):
#                     mindis = dis[node]
#                     selectednode = node
#         if selectednode == None:
#             break
#         flags[selectednode] = True
#         if selectednode in srcnodes:
#             break
#     if selectednode == None:
#         return []
#     ret = []
#     last = selectednode
#     while last != outnode:
#         ap = pathlinks[last]
#         ret.append(ap)
#         last = links[ap][0]
#     ret.append(dstport)
#     return ret

def shortestpath_tap2(output=None):
    nodes = predef.nodes
    links = predef.links
    prepath = predef.selectedshortestpath
    innode = prepath[0][0]
    if output==None:
        outnodes = predef.statemachine_pos
    else:
        outnodes = [output,]
    if innode in outnodes:
        return [(innode,'tap')]
    dis = dict.fromkeys(nodes.keys(), -1)
    dis[innode] = 0
    flags = dict.fromkeys(nodes.keys(), False)
    flags[innode] = True
    selectednode = innode
    pathlinks = {}
    while True:
        for port in nodes[selectednode]:
            aport = (selectednode, port)
            p2 = links.get(aport)
            if p2 != None:
                n2 = p2[0]
                if not flags[n2]:
                    dis_new = dis[selectednode] + __weight(aport)
                    if dis[n2] == -1 or dis[n2] > dis_new:
                        dis[n2] = dis_new
                        pathlinks[n2] = aport
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
        if selectednode in outnodes:
            break
    if selectednode == None:
        return []
    ret = [(selectednode,'tap')]
    last = selectednode
    while last != innode:
        ap = pathlinks[last]
        if ap in predef.selectedshortestpath:
            break
        ret.append(ap)
        last = ap[0]
    ret.reverse()
    return ret

#
# def tcp_tap(inport, outport):
#     path = shortestpath(inport, outport, weight=getweight)
#     incweight_path(path)
#     pathmap = dict(path)
#
#     tap_path = None
#     for tapdst in predef.statemachine_pos:
#         ret = shortestpath_tap((tapdst, 'tap'), pathmap.keys())
#         if tap_path == None:
#             tap_path = ret
#         elif len(ret) < len(tap_path):
#             tap_path = ret
#     incweight_path(tap_path)
#
#     predef.taprulecount = predef.taprulecount + len(tap_path) - 1
#
#     tapport = tap_path[0]
#     tapnode = tapport[0]
#     pathmap[tapnode] = (pathmap[tapnode], tapport[1])
#     for n, p in tap_path[1:]:
#         assert not pathmap.has_key(n)
#         pathmap[n] = p
#     return pathmap



def __weight(sw_port):
    assert predef.selectedshortestpath!=None
    if sw_port in predef.selectedshortestpath:
        return 0
    pport = predef.links.get(sw_port)
    assert pport!=None
    sw = sw_port[0]
    swrs = predef.oldsaveflowrules.get(sw)
    if swrs!=None and swrs.get((predef.selectedsrcip,predef.selecteddstip))==sw_port[1]:
        return 1
    else:
        return 1+predef.beta


def tcp_tap2(inport, outport):
    path = shortestpath(inport, outport, weight=defaultwight)

    if len(path)==0:
        return dict()

    pathmap = dict(path)

    predef.selectedshortestpath=path
    assert path[0][0]==inport[0]

    tap_path=None
    if predef.firstrun:
        tap_path = shortestpath_tap2()
    else:
        tap_path = shortestpath_tap2(output=predef.savetapport[(inport,outport)])

    if len(tap_path)==0:
        return pathmap
    if predef.firstrun:
        a=tap_path[-1][0]
        predef.savetapport[(inport,outport)]=a

    predef.taprulecount = predef.taprulecount + len(tap_path) - 1

    tapport = tap_path[0]
    tapnode = tapport[0]

    pathmap[tapnode] = (pathmap[tapnode], tapport[1])
    for n, p in tap_path[1:]:
        assert not pathmap.has_key(n)
        pathmap[n] = p
    return pathmap


def pre_generate_flows():
    of = ofproto_v1_3
    ofp = ofproto_v1_3_parser
    Match = ofp.OFPMatch
    ActionOutput = ofp.OFPActionOutput
    alltable = dict.fromkeys(predef.nodes.keys(), None)
    for i in alltable:
        alltable[i]=[]
    # default table-miss
    # emptymatch = Match()
    # puntactions = [ActionOutput(of.OFPP_CONTROLLER, of.OFPCML_NO_BUFFER)]
    # for a in alltable:
    #     alltable[a] = [(0, emptymatch, puntactions)]
    # arp broadcast
    # arpMatch = Match(eth_type=0x0806)
    # arppath = arpspt()
    # for a, ports in arppath.items():
    #     outputs = [ActionOutput(x) for x in ports]
    #     alltable[a].append((1, arpMatch, outputs))
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

    # shortest path tcp + tap
    items = predef.ip2portTable.items()
    for ip1, port1 in items:
        for ip2, port2 in items:
            if ip1 != ip2:
                predef.selectedsrcip=ip1
                predef.selecteddstip=ip2
                pathmap = tcp_tap2(port1, port2)
                for a in pathmap:
                    ipMatch = Match(eth_type=0x0800, ipv4_src=ip1, ipv4_dst=ip2, ip_proto=6)
                    savetable(a, ip1, ip2, pathmap[a])
                    if isinstance(pathmap[a], tuple):
                        alltable[a].append((2, ipMatch, [ActionOutput(p) for p in pathmap[a]]))
                    else:
                        alltable[a].append((2, ipMatch, [ActionOutput(pathmap[a])]))
    return alltable

def savetable(a,src,dst,output):
    t = predef.saveflowrules.get(a)
    if t==None:
        predef.saveflowrules[a]={(src,dst):output}
    else:
        t[(src,dst)]=output



################# inc weight ##############


_weight = {}


def getweight(port):
    global _weight
    if _weight.get(port) == None:
        return 1
    else:
        return _weight[port]


def incweight(port):
    global _weight
    if _weight.get(port) == None:
        _weight[port] = 2
    else:
        _weight[port] = _weight[port] + 1


def incweight_path(path):
    for i in path:
        incweight(i)

################# networkx show topology ##############


def showtopo(topo):
    labels = {}
    for n in topo.adj:
        labels[n] = n
    pos = nx.spring_layout(topo)
    nx.draw(topo, pos=pos)
    nx.draw_networkx_labels(topo, pos, labels=labels)
    plt.show()


def switchdown(s):
    ports = predef.nodes[s]
    for p in ports:
        pp = predef.links.get((s, p))
        if pp!=None:
            predef.links.pop((s,p))
            predef.links.pop(pp)
    predef.nodes.pop(s)

def linkdown(s1,s2):
    ports = predef.nodes[s1]
    for p in ports:
        pp = predef.links.get((s1,p))
        if pp!=None and pp[0]==s2:
            predef.links.pop((s1,p))
            predef.links.pop(pp)



def genmininetconfig(sw_num,host_num_list,addlink):
    fp = open('gen/sw.config','w+')
    fp.write('%d\n'%sw_num)
    for i in host_num_list:
        fp.write('%d '%i)
    fp.write("\n")
    for link in addlink:
        fp.write("%s %s\n"%link)
    fp.close()


# Cwix 10 10

def saveflowrulestofile(flowrules,filename):
    fp=open(filename,'w+')
    for i in flowrules:
        swtable = flowrules[i]
        for sd in swtable:
            portorports = swtable[sd]
            if isinstance(portorports,tuple):
                x=["%d"%predef.portidmap[(i,k)] for k in portorports]
                port=','.join(x)
            else:
                port = "%d"%(predef.portidmap[(i,portorports)])
            fp.write("%s %s %s %s\n"%(i,sd[0],sd[1],port))
    fp.close()


def maptableport(sw,portorports):
    if isinstance(portorports,tuple):
        x = ["%d"%(predef.portidmap[(sw,x)]) for x in portorports]
        return ','.join(x)
    else:
        return "%d"%(predef.portidmap[(sw,portorports)])

if __name__ == "__main__":
    predef.nodes = {}
    predef.links = {}
    predef.ip2portTable = {}
    nodes = predef.nodes
    links = predef.links
    ip2portTable = predef.ip2portTable
    topology_name = "Cwix" #"Digex"  Cwix Dfn
    filename = "/home/yutao/Documents/topologyzoo-graphml2/sources/" + topology_name + ".graphml"
    topo = nx.read_graphml(filename).to_undirected()


    i = 0
    if i == 1:
        showtopo(topo)
        sys.exit(0)

    predef.statemachine_pos = {'n16'}# 11 13 23 6 1625
    willdownsw = {}

    for n in topo.adj:
        predef.nodes[n] = []

    for s in predef.statemachine_pos:
        predef.nodes[s].append('tap')

    allocedportid = dict.fromkeys(topo.adj,1)
    addlink = []
    for n in topo.adj:
        for pn in topo.adj[n]:
            km = topo.adj[n][pn]
            eid = km.get('id')
            if eid == None:
                assert isinstance(km, dict)
                eid = ','.join(km.keys())
                assert eid.startswith('e')
            predef.nodes[n].append(eid)
            sw_port = (n,eid)
            predef.links[sw_port] = (pn, eid)
            if not predef.portidmap.has_key(sw_port):
                id_n = allocedportid[n]
                allocedportid[n]=allocedportid[n]+1
                predef.portidmap[sw_port]=id_n
                id_pn = allocedportid[pn]
                allocedportid[pn]=allocedportid[pn]+1
                predef.portidmap[(pn,eid)]=id_pn
                addlink.append((n,pn))

    keys = nodes.keys()
    # for i in range(40):
    #     hosti = "192.168.0.%d" % i
    #     hostisw = keys[random.randint(0, len(keys) - 1)]
    #     while hostisw in willdownsw:
    #         hostisw = keys[random.randint(0, len(keys) - 1)]
    #     nodes[hostisw].append(hosti)
    #     ip2portTable[hosti] = (hostisw, hosti)
    host_num_list = []
    for i in range(len(keys)):
        hosti = "10.0.0.%d" % (i+1)
        hostisw = "n%d"%i  ##FIXME bug
        if hostisw in willdownsw:
            continue
        host_num_list.append(i+1)
        nodes[hostisw].append(hosti)
        s_p=(hostisw, hosti)
        ip2portTable[hosti] =s_p
        predef.portidmap[s_p]=allocedportid[hostisw]
        allocedportid[hostisw]=allocedportid[hostisw]+1
        addlink.append(('h%d'%(i+1),hostisw))

    # fix the tap port id
    for i in predef.statemachine_pos:
        predef.portidmap[(i,'tap')]=allocedportid[i]

    genmininetconfig(len(keys),host_num_list,addlink)

    for n in predef.nodes:
        predef.nodes[n] = tuple(predef.nodes[n])

    print(predef.nodes)
    print(predef.links)
    print(ip2portTable)

    predef.taprulecount = 0
    predef.saveflowrules = dict()
    predef.savetapport = dict()
    alltable = pre_generate_flows()
    count = 0
    for k in alltable.values():
        count = count + len(k)
    print("(%d,%d,)" % (count, predef.taprulecount))

    flowcount1 = count

    print(len(nodes))

    linksize = len(links)
    nodesize = len(nodes)

    for k in willdownsw:
        switchdown(k)
    # linkdown('n6','n16')

    savelinkdown=[]

    random.seed(11)
    lk = links.keys()
    for i in range(1):
        de = lk[random.randint(0,len(lk)-1)]
        if not links.has_key(de):
            continue
        pp = links[de]
        links.pop(de)
        links.pop(pp)
        savelinkdown.append((de,pp))

    flowrules1 = predef.saveflowrules

    saveflowrulestofile(flowrules1,'gen/rules1.txt')

    predef.firstrun = False
    taprulecount1 = predef.taprulecount

    countlist = []
    taprclist = []
    flowcountlist=[]
    timelist=[]
    for i in range(0,20):
        start_time=time.time()
        predef.beta = i
        predef.taprulecount = 0
        predef.oldsaveflowrules = flowrules1
        predef.saveflowrules = dict()
        alltable = pre_generate_flows()
        count = 0
        for k in alltable.values():
            count = count + len(k)
        print("(%d,%d,)" % (count, predef.taprulecount))
        print(len(nodes))

        flowcountlist.append(count)

        taprc = predef.taprulecount
        taprclist.append(taprc)

        flowrules2 = predef.saveflowrules

        diffstr = ""
        count = 0
        for i in predef.nodes:
            table2= flowrules2.get(i)
            table1=flowrules1.get(i)
            if table1 == None and table2 !=None:
                for k in table2:
                    diffstr=diffstr+"n %s %s %s %s\n"%(i,k[0],k[1],maptableport(i,table2[k]))
                    count = count +1
            elif table1 != None and table2 ==None:
                for k in table1:
                    diffstr=diffstr+"d %s %s %s %s\n" % (i, k[0], k[1], maptableport(i,table1[k]))
                    count = count + 1
            elif table1 != None and table2 !=None:
                for k in table2:
                    if table1.get(k)==None:
                        diffstr=diffstr+"n %s %s %s %s\n" % (i, k[0], k[1], maptableport(i,table2[k]))
                        count = count + 1
                    elif table1[k]!=table2[k]:
                        diffstr=diffstr+"n %s %s %s %s\n" % (i, k[0], k[1], maptableport(i,table2[k]))
                        diffstr=diffstr+"d %s %s %s %s\n" % (i, k[0], k[1], maptableport(i,table1[k]))
                        count = count + 2
                for k in table1:
                    if table2.get(k)==None:
                        diffstr=diffstr+"d %s %s %s %s\n" % (i, k[0], k[1], maptableport(i,table1[k]))
                        count = count + 1

        # fp = open('gen/diffrule%d.txt' % i, 'w+')
        # fp.write(diffstr)
        # fp.close()
        print(diffstr)
        print(count)
        countlist.append(count)
        timelist.append(time.time()-start_time)
    print(countlist)
    print(taprclist)
    print(flowcountlist)
    print("tap = %d all = %d"%(taprulecount1,flowcount1))
    print("linksize = %d nodesize = %d"%(linksize,nodesize))
    print(savelinkdown)
    print(timelist)