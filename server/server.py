#!/usr/bin/env python


from autobahn.twisted.websocket import WebSocketServerProtocol, \
					   WebSocketServerFactory
import sys
import os
from twisted.python import log
from twisted.internet import reactor

from autobahn.twisted.websocket import WebSocketClientProtocol, \
									   WebSocketClientFactory
from json import dumps
from ws4py.client.threadedclient import WebSocketClient

from threading import Thread
import socket
import webportal
import json
import MySQLdb

from subprocess import Popen


Sessions = []
Robots = []


def getPort():
		for port in range(7000,8000):  
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			result = sock.connect_ex(('localhost', port))
			if result != 0:
				sock.close()
				return port
			sock.close()

def is_json(data):
  try:
    json_object = json.loads(data)
  except ValueError, e:
    return False
  return True


class MyServerProtocol(WebSocketServerProtocol):
	
	global database

	def onConnect(self, request):
		print("SERVER: Client connecting: {0}".format(request.peer))	

	def onOpen(self):
		print("SERVER: Connection opened")

	def onMessage(self, payload, isBinary):
		
		if isBinary:
			print("SERVER: Binary message received: {0} bytes".format(len(payload)))
		else:
			print("SERVER: Text message received: {0}".format(payload.decode('utf8')))

		self.parseData = payload.split('|')

		if len(self.parseData) != 0:
			
			self.id = self.parseData[0].split(':')
			
			if self.id[1] == 'ROBOT':
				#Create object robot -> append to list Robots -> send message
				if self.id[0] == 'REGISTRATION':
					self.rob = webportal.Robot(self.parseData[1], self.parseData[2], self, False)
					Robots.append(self.rob)
					self.Message = 'REGISTRATION:SERVER|OK|' + self.parseData[1]					
					self.sendMessage(self.Message.encode('utf8'))

					#Bridge - argv[1] - login, argv[2] - port
					self.bridgeProcess = Popen(['./connectionmain.py', self.parseData[1], str(port), 'shell=True'])
					self.ses = webportal.Session(self.rob, self.bridgeProcess)
					Sessions.append(self.ses)


			#Registration rosbridge process for robot
			elif self.id[1] == 'PROCESS':
				if self.id[0] == 'REGISTRATION':
					self.robot = "hroch14"
					for ses in Sessions:
						#Create session
						if str(ses.getBridgePID()) == str(self.parseData[1]):				
							ses.addBridgeGetway(self)
							ses.saveBridgePort(self.parseData[2])
							self.Message = 'SERVER:BRIDGECONNECTION|' + self.parseData[2]
							for robot in ses.getRobots():
								robot.getGetway().sendMessage(self.Message.encode('utf8'))
							self.Message = 'REGISTRATION:SERVER|OK|' + self.parseData[1]
							self.sendMessage(self.Message.encode('utf8'))
							self.robot = ses.getRobots()[0].getID()

							self.cursor = database.cursor()

							try:
								self.sql_bridge = ("""INSERT INTO `rosbridges` (`name`, `protocol_id`, `host`, `port`, `rosauth`, `created`, `modified`)
												 VALUES ("bridge_"%s, 1, "37.205.11.196", %s, NULL, NOW(), NOW())""", (self.robot, int(ses.getBridgePort())))

								self.cursor.execute(*self.sql_bridge)
								database.commit()

								#Pustin stream, vlozim ho do session
								self.stream = Popen(['./streamserver.py', '37.205.11.196', str(port), 'shell=True'])
								for ses in Sessions:
									if str(ses.getBridgePID()) == str(self.parseData[1]):
										ses.addStreamPID(self.stream)

								print "SERVER: Rosbridge import OK"

							except MySQLdb.Error, e:
								print e
								database.rollback()



			elif self.id[1] == 'STREAM':
				if self.id[0] == 'REGISTRATION':
					self.robot = "hroch14"
					for ses in Sessions:
						if str(ses.getStreamPID()) == str(self.parseData[1]):
							ses.saveStreamPort(self.parseData[2])
							self.robot = ses.getRobots()[0].getID()
							self.Message = 'REGISTRATION:OK'
							self.sendMessage(self.Message.encode('utf8'))

							self.Message = 'SERVER:STREAMCONNECTION|' + self.parseData[2]
							for robot in ses.getRobots():
								robot.getGetway().sendMessage(self.Message.encode('utf8'))

							self.cursor = database.cursor()
							self.bridge_id = 1;
							self.mjpeg_id = 1;

							try:
								self.sql_mjpeg = ("""INSERT INTO `mjpegs` (`name`, `host`, `port`, `created`, `modified`)
													 VALUES ("mjpeg_"%s, "37.205.11.196", %s, NOW(), NOW())""", (self.robot, int(ses.getStreamPort())))

								self.cursor.execute(*self.sql_mjpeg)
								database.commit()

								self.sql = ("""SELECT id FROM rosbridges WHERE name="bridge_"%s""", (self.robot))
								self.cursor.execute(*self.sql)
								self.bridge_id = int(self.cursor.fetchone()[0])

								self.sql = ("""SELECT id FROM mjpegs WHERE name="mjpeg_"%s""", (self.robot))
								self.cursor.execute(*self.sql)
								self.mjpeg_id = int(self.cursor.fetchone()[0])

								self.sql = ("""INSERT INTO environments (name, `rosbridge_id`, mjpeg_id, created, modified)
										  	   VALUES (%s, %s, %s, NOW(), NOW())""", (self.robot, self.bridge_id, self.mjpeg_id))

								self.cursor.execute(*self.sql)
								database.commit()

								print "SERVER: Mjpeg import OK"
								print "SERVER: Environments CREATED OK"

							except MySQLdb.Error, e:
								print e
								database.rollback()


			else:
				print("SERVERERROR: WRONG IDENTIFICATION CLIENT IN PROTOCOL")
			
									
	def onClose(self, wasClean, code, reason):
			print("SERVER: WebSocket connection closed: {0}".format(reason))


if __name__ == '__main__':

	print("SERVER START:" + str(sys.argv[1]))
	port = sys.argv[1]

	database = MySQLdb.connect(host='localhost', user='root', passwd='athlon', db='rms')
	cursor = database.cursor()

	#print is_json("{}")              #prints True

	factory = WebSocketServerFactory('ws://localhost:' + port, debug = False)
	factory.protocol = MyServerProtocol
	reactor.listenTCP(int(port), factory)
	reactor.run()













