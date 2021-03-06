#!/usr/bin/python2
# -*- coding: utf-8 -*-

# nodes={1:(1,2),2:(2,3,4)}
# nodes={2:(1,2,3),1:(1,2,3,4),4:(2,1),3:(1,2,3),6:(1,2,3),5:(5,6,1,2,3,4),7:(3,4,5,1,2)}

# links={(1,1):(2,3)}
# links={(1,1):(2,1),(2,1):(1,1),(1,2):(5,1),(3,1):(5,2),(2,2):(3,2),(1,3):(7,2),(4,1):(5,4),(2,3):(7,1),(3,2):(2,2),(5,1):(1,2),(4,2):(3,3),(3,3):(4,2),(6,1):(5,5),(5,2):(3,1),(5,3):(7,3),(7,1):(2,3),(7,2):(1,3),(6,3):(7,5),(5,4):(4,1),(7,3):(5,3),(5,5):(6,1),(7,5):(6,3)}


# ip2portTable={'192.168.1.1':(2,4)}
#
# mac2portTable={'00:00:00:00:1':(2,4)}
#
# port2hostTable={
#     (2,4) : {'ip':'192.168.1.1','mac':'00:00:00:00:1'}
# }

# ip2portTable={"192.168.56.1":(7,4),"192.168.56.2":(6,2),"192.168.56.3":(5,6)}

# mac2portTable={"ce:b7:a0:8b:4a:0f":(7,4),"42:b7:7a:68:98:e2":(6,2),"32:ad:11:47:6c:b4":(5,6)}

# port2hostTable={(7,4):{'ip':"192.168.56.1",'mac':"ce:b7:a0:8b:4a:0f"},(6,2):{'ip':"192.168.56.2",'mac':"42:b7:7a:68:98:e2"},(5,6):{'ip':"192.168.56.3",'mac':"32:ad:11:47:6c:b4"}}


nodes = {2: (1, 2, 3, 5), 1: (1, 2, 3, 4), 4: (1, 2, 4), 3: (1, 2, 3, 5), 6: (5, 1, 2, 3), 5: (5, 6, 8, 1, 2, 3, 4),
         7: (3, 4, 5, 1, 2, 7)}
links = {(1, 1): (2, 1), (2, 1): (1, 1), (1, 2): (5, 1), (2, 2): (3, 2), (1, 3): (7, 2), (3, 1): (5, 2), (3, 2): (2, 2),
         (2, 3): (7, 1), (4, 1): (5, 4), (4, 2): (3, 3), (3, 3): (4, 2), (5, 1): (1, 2), (5, 2): (3, 1), (6, 1): (5, 5),
         (7, 1): (2, 3), (5, 3): (7, 3), (7, 2): (1, 3), (6, 3): (7, 5), (5, 4): (4, 1), (5, 5): (6, 1), (7, 3): (5, 3),
         (7, 5): (6, 3)}
ip2portTable = {"192.168.56.3": (5, 6), "192.168.56.1": (7, 4), "192.168.56.13": (3, 5), "192.168.56.2": (6, 2),
                "192.168.56.6": (6, 5), "192.168.56.7": (7, 7), "192.168.56.12": (2, 5), "192.168.56.14": (4, 4),
                "192.168.56.5": (5, 8)}
mac2portTable = {"d6:d5:ae:0a:44:66": (5, 6), "da:66:ae:ec:e1:db": (7, 4), "92:3f:34:21:ef:40": (3, 5),
                 "26:1c:11:db:25:e4": (6, 2), "f2:0d:d9:b9:01:31": (6, 5), "da:a8:d8:8c:e1:7b": (7, 7),
                 "22:90:05:c0:51:75": (2, 5), "d6:ea:86:d9:3b:39": (4, 4), "d6:82:59:e3:9c:f1": (5, 8)}
port2hostTable = {(5, 6): {'ip': "192.168.56.3", 'mac': "d6:d5:ae:0a:44:66"},
                  (7, 4): {'ip': "192.168.56.1", 'mac': "da:66:ae:ec:e1:db"},
                  (3, 5): {'ip': "192.168.56.13", 'mac': "92:3f:34:21:ef:40"},
                  (6, 2): {'ip': "192.168.56.2", 'mac': "26:1c:11:db:25:e4"},
                  (6, 5): {'ip': "192.168.56.6", 'mac': "f2:0d:d9:b9:01:31"},
                  (7, 7): {'ip': "192.168.56.7", 'mac': "da:a8:d8:8c:e1:7b"},
                  (2, 5): {'ip': "192.168.56.12", 'mac': "22:90:05:c0:51:75"},
                  (4, 4): {'ip': "192.168.56.14", 'mac': "d6:ea:86:d9:3b:39"},
                  (5, 8): {'ip': "192.168.56.5", 'mac': "d6:82:59:e3:9c:f1"}}

