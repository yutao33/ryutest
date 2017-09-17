#!/usr/bin/python2
# -*- coding: utf-8 -*-

from broccoli import *
import time as Time

@event
def testtt(i):
    print(i)

bc = Connection('127.0.0.1:47758')

recv = 0
while True:
    bc.processInput();
    if recv == 2:
        break
    Time.sleep(1)
