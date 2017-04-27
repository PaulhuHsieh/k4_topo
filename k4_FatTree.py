#!/usr/bin/python
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.node import RemoteController
from mininet.node import Node
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.cli import CLI

import logging
import os
import random

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger( __name__ )

class MyTopo( Topo ):

	coreSwitchList = []
	aggrSwitchList = []
	edgeSwitchList = []
	hostList = []
	hostIPList = []

	#Initialization
	def __init__( self ):
		self.kNUM = 4
		self.coreNUM = 4
		self.aggrNUM = 8
		self.edgeNUM = 8
		self.hostNUM = 32
		Topo.__init__( self )

	#Build up topology
	def topoBuildUp( self ):
		logger.debug("topoBuildUp(): Start creating core switches.")
		self.createCoreSwitch()
		logger.debug("topoBuildUp(): Start creating aggregation switches.")
		self.createAggrSwitch()
		logger.debug("topoBuildUp(): Start creating edge switches.")
		self.createEdgeSwitch()
		logger.debug("topoBuildUp(): Start creating hosts.")
		self.createHost()
		logger.debug("topoBuildUp(): Start creating links.")
		self.createLink()

	#Add switches and hosts in topology
	def createCoreSwitch(self):
		leading = "s100"
		for it in range(1,self.coreNUM + 1):
			self.coreSwitchList.append(self.addSwitch(leading + str(it)))

	def createAggrSwitch(self):
		leading = "s200"
		for it in range(1,self.aggrNUM + 1):
			self.aggrSwitchList.append(self.addSwitch(leading + str(it)))

	def createEdgeSwitch(self):
		leading = "s300"
		for it in range(1,self.edgeNUM + 1):
			self.edgeSwitchList.append(self.addSwitch(leading + str(it)))

	def createHost(self):
#		logger.debug("createHost(): Add test host")
#		self.addHost("test01")

		leading = "h"
		for field in range(1, self.coreNUM + 1):
			for num in range(1, self.hostNUM/self.coreNUM + 1):
				self.hostList.append(self.addHost(leading + str(field) + str(num)))

	#Add links
	def createLink( self ):
		logger.debug("createLink(): core-aggr")
		for x in range(0, self.aggrNUM, 2):
			self.addLink(self.coreSwitchList[0], self.aggrSwitchList[x])
			self.addLink(self.coreSwitchList[1], self.aggrSwitchList[x])
		for x in range(1, self.aggrNUM, 2):
			self.addLink(self.coreSwitchList[2], self.aggrSwitchList[x])
			self.addLink(self.coreSwitchList[3], self.aggrSwitchList[x])

		logger.debug("createLink(): aggr-edge")
		for x in range(0, self.aggrNUM, 2):
			self.addLink(self.aggrSwitchList[x], self.edgeSwitchList[x])
			self.addLink(self.aggrSwitchList[x], self.edgeSwitchList[x+1])
			self.addLink(self.aggrSwitchList[x+1], self.edgeSwitchList[x])
			self.addLink(self.aggrSwitchList[x+1], self.edgeSwitchList[x+1])

		logger.debug("createLink(): edge-host")
		for x in range (0,self.edgeNUM):
			self.addLink(self.edgeSwitchList[x], self.hostList[x*4])
			self.addLink(self.edgeSwitchList[x], self.hostList[x*4 + 1])
			self.addLink(self.edgeSwitchList[x], self.hostList[x*4 + 2])
			self.addLink(self.edgeSwitchList[x], self.hostList[x*4 + 3])

#		logger.debug("createLink(): Add a link between test host & core switch s1001")
#		self.addLink("s1001", "test01")

	def set_OF13( self ):
		self.set_SWList_OF13( self.coreSwitchList )
		self.set_SWList_OF13( self.aggrSwitchList )
		self.set_SWList_OF13( self.edgeSwitchList )

	def set_SWList_OF13( self, sw_List ):
		for single_sw in sw_List:
			cmd = "sudo ovs-vsctl set bridge %s protocols=OpenFlow13" % single_sw
			os.system(cmd)
		

def perfTest():
	logger.debug("perfTest(): Declare a fat tree")
	fatTree = MyTopo()

	logger.debug("perfTest(): Fat tree build up")
	fatTree.topoBuildUp()

	logger.debug("perfTest(): Mininet initialization")
	net = Mininet(topo=fatTree, link=TCLink, controller=None)

	logger.debug("perfTest(): Add remote controller #BLOCKED")
	#net.addController("c01", controller=RemoteController, ip="192.168.1.10", port=6633)

	logger.debug("perfTest(): Mininet start")
	net.start()

	fatTree.set_OF13()

	ipPrefix = "10.0.0."
	ipPostfix = 32
	for host_name in fatTree.hostList:
		host_IP_tmp = ipPrefix + str(ipPostfix)
		hostTemp = net.get(host_name)
		hostTemp.setIP(host_IP_tmp)
		fatTree.hostIPList.append(host_IP_tmp)
		ipPostfix += 1

	while True:
                traffic_enable = open("traffic_enable", "r")
                if traffic_enable.readline().find("yes") == -1:
                        break

                i = random.randint(1, len(fatTree.hostList))
                host_tmp = net.get(fatTree.hostList[i - 1])
                j = i

                while j == i:
                        j = random.randint(1, len(fatTree.hostList))

                conmand = "ping -c 1 -W 1 %s" % fatTree.hostIPList[j - 1]
                host_tmp.cmd(conmand)
                print "%s ---> %s" % (fatTree.hostIPList[i - 1], fatTree.hostIPList[j - 1])
	
	CLI(net)

	net.stop()

if __name__ == '__main__':
	setLogLevel('info')
	perfTest()

topos = { 'mytopo': ( lambda: MyTopo() ) }

