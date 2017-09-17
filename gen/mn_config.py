#!/usr/bin/python
import os
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8',
                   autoStaticArp=True)

    info( '*** Adding controller\n' )
    c0=net.addController(name='c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      protocol='tcp',
                      port=6633)

    fp=open('sw.config')
    lines = fp.readlines()

    info( '*** Add switches\n')
    sw_num=int(lines[0])
    s= dict()
    for i in range(sw_num):
        s[i]=net.addSwitch('s%d'%(i+1),cls=OVSKernelSwitch)
    #s1 = net.addSwitch('s1', cls=OVSKernelSwitch)

    info( '*** Add hosts\n')
    hosts_num = lines[1].split()
    h=dict()
    for hostnum in hosts_num:
        num = int(hostnum)
        h[num]=net.addHost('h%d'%num, cls=Host, ip='10.0.0.%d'%num, defaultRoute=None)
    #h3 = net.addHost('h3', cls=Host, ip='192.168.56.3', defaultRoute=None)

    info( '*** Add links\n')
    s1s2 = {'bw':1000}
    # net.addLink(s1, s2, cls=TCLink , **s1s2)
    for linkstr in lines[2:]:
        a1,a2=linkstr.split()
        a1num=int(a1[1:])
        a2num=int(a2[1:])
        if a1.startswith('h'):
            a1 = h[a1num]
        else:
            a1 =s[a1num]
        if a2.startswith('h'):
            a2 = h[a2num]
        else:
            a2 =s[a2num]
        net.addLink(a1,a2,cls=TCLink,**s1s2)


    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    for i in range(sw_num):
        net.get('s%d'%(i+1)).start([c0])
    #net.get('s1').start([c0])



    info( '*** Post configure switches and hosts\n')


    # os.system('ip link add s1-eth4 type veth peer name s1-eth4-peer')
    # os.system('ovs-vsctl add-port s1 s1-eth4')
    # os.system('ifconfig s1-eth4 up')
    # os.system('ifconfig s1-eth4-peer up')
    CLI(net)
    # os.system('ip link del s1-eth4')
    net.stop()

if __name__ == '__main__':
    setLogLevel( 'info' )
    myNetwork()

