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


nodes = {2: (1, 2, 3, 4), 1: (1, 2, 3, 4), 4: (1, 2, 3), 3: (1, 2, 3, 4, 5), 6: (4, 5, 1, 2, 3),
         5: (5, 6, 7, 1, 2, 3, 4), 7: (3, 4, 5, 6, 1, 2)}
links = {(1, 1): (2, 1), (2, 1): (1, 1), (1, 2): (5, 1), (2, 2): (3, 2), (3, 1): (5, 2), (1, 3): (7, 2), (3, 2): (2, 2),
         (2, 3): (7, 1), (4, 1): (5, 4), (3, 3): (4, 2), (5, 1): (1, 2), (4, 2): (3, 3), (5, 2): (3, 1), (6, 1): (5, 5),
         (5, 3): (7, 3), (7, 1): (2, 3), (6, 3): (7, 5), (5, 4): (4, 1), (7, 2): (1, 3), (5, 5): (6, 1), (7, 3): (5, 3),
         (7, 5): (6, 3)}
ip2portTable = {"192.168.56.12": (2, 4), "192.168.56.13": (3, 5), "192.168.56.1": (7, 4), "192.168.56.14": (4, 3),
                "192.168.56.5": (5, 7), "192.168.56.3": (5, 6), "192.168.56.7": (7, 6), "192.168.56.6": (6, 5),
                "192.168.56.2": (6, 2)}
mac2portTable = {"72:67:21:a6:5a:4b": (2, 4), "76:5a:23:b5:a5:14": (3, 5), "0e:48:51:63:40:60": (7, 4),
                 "d6:99:33:db:4f:33": (4, 3), "f6:9c:05:50:3d:ec": (5, 7), "fa:92:a9:b9:ae:72": (5, 6),
                 "de:09:f9:81:36:39": (7, 6), "06:97:27:b4:a3:db": (6, 5), "fa:18:d8:d7:2f:df": (6, 2)}
port2hostTable = {(2, 4): {'ip': "192.168.56.12", 'mac': "72:67:21:a6:5a:4b"},
                  (3, 5): {'ip': "192.168.56.13", 'mac': "76:5a:23:b5:a5:14"},
                  (7, 4): {'ip': "192.168.56.1", 'mac': "0e:48:51:63:40:60"},
                  (4, 3): {'ip': "192.168.56.14", 'mac': "d6:99:33:db:4f:33"},
                  (5, 7): {'ip': "192.168.56.5", 'mac': "f6:9c:05:50:3d:ec"},
                  (5, 6): {'ip': "192.168.56.3", 'mac': "fa:92:a9:b9:ae:72"},
                  (7, 6): {'ip': "192.168.56.7", 'mac': "de:09:f9:81:36:39"},
                  (6, 5): {'ip': "192.168.56.6", 'mac': "06:97:27:b4:a3:db"},
                  (6, 2): {'ip': "192.168.56.2", 'mac': "fa:18:d8:d7:2f:df"}}