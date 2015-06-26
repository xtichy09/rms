#!/usr/bin/python


from autobahn.twisted.websocket import WebSocketServerProtocol, \
									   WebSocketServerFactory

from autobahn.twisted.websocket import WebSocketClientProtocol, \
									   WebSocketClientFactory

from multiprocessing import Process

import sys
import os
from twisted.python import log
from twisted.internet import reactor
import json
from ws4py.client.threadedclient import WebSocketClient
import socket
import webportal
from datetime import datetime
from subprocess import Popen



Robot = []
Clients = []
API = []
AccessLogins = []
streamPort = []
streamProcess = []



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


#Server for webclient
class MyServerProtocol(WebSocketServerProtocol):
	

	def onConnect(self, request):
		print("PROCESS_BRIDGE: Client connecting: {0}".format(request.peer))
			
	def onOpen(self):
		print("PROCESS_BRIDGE: WebSocket connection open.")

	def onMessage(self, payload, isBinary):
		global port
		if isBinary:
			print("PROCESS_BRIDGE: Binary message received: {0} bytes".format(len(payload)))
		else:
			print("PROCESS_BRIDGE: Text message received: {0}".format(payload.decode('utf8')))

		if(payload[0] == '"'):
			payload = payload[1:-1]

		if is_json(payload):
			if Robot:
				Robot[0].sendMessage(payload.encode('utf8'))
			else:
				print "PROCESS_BRIDGE: ROBOT IS NOT CONNECTED!"
			Clients[0] = self

		else:

			self.parseData = payload.split('|')

			if len(self.parseData) != 0:
				self.id = self.parseData[0].split(':')

				if(self.id[1] == 'ROBOT'):
					if(self.id[0] == 'REGISTRATION'):
						Robot.append(self)
						self.Message = 'REGISTRATION:BRIDGE|OK|' + self.parseData[1]
						self.sendMessage(self.Message.encode('utf8'))

					elif(self.id[0] == 'MESSAGE'):
						if Clients:
							Clients[0].sendMessage(self.parseData[1].encode('utf8'))
							print("ODOSIELAM SPRAVU NA WEB!!")

				
	def onClose(self, wasClean, code, reason):
		#TODO - odebrat ze seznamu
		print("WebSocket connection closed: {0}".format(reason))


#Client for API server
class MyClientProtocol(WebSocketClientProtocol):
	

	state = 0

	def onConnect(self, response):
		print("PROCESS_API: Server connected: {0}".format(response.peer))


	def onOpen(self):
		print("PROCESS_API: Start websocket connection to server.")

		global port
		API.append(self)
		self.Message = 'REGISTRATION:PROCESS|' + str(os.getpid()) + '|' + str(port)
		self.sendMessage(self.Message.encode('utf8'))


	def onMessage(self, payload, isBinary):
		if isBinary:
			 print("PROCESS_API: Binary message received: {0} bytes".format(len(payload)))
		else:
			 print("PROCESS_API: Text message received: {0}".format(payload.decode('utf8')))
	
		self.parseData = payload.split('|')

		if len(self.parseData) != 0:
			self.id = self.parseData[0].split(':')
			
			if self.id[0] == 'REGISTRATION':
				if self.parseData[1] == 'OK':
					print "PROCESS-%d: Registration OK" % os.getpid()
				
	def onClose(self, wasClean, code, reason):
			print("PROCESS_API: WebSocket connection closed: {0}".format(reason))


class Client:
	
	def __init__(self , getway, login):
		self.getway = getway
		self.ID = login

	def getGetway(self):
		return self.getway

	def getID(self):
		return self.ID


if __name__ == '__main__':


	print "PROCESS: START NEW PROCESS |%s|%s|%d" % (sys.argv[1], sys.argv[2], os.getpid())

	global port
	#Init lepsie to vyries
	Clients.append(0)

	ApiFactory = WebSocketClientFactory('ws://localhost:' + str(sys.argv[2]), debug = False)
	ApiFactory.protocol = MyClientProtocol
	reactor.connectTCP("127.0.0.1", int(sys.argv[2]), ApiFactory)
		
	#Interface for Web client
	#TODO - IP|PORT
	port = getPort()
	WebFactory = WebSocketServerFactory('ws://localhost:'+str(port), debug = False)
	WebFactory.protocol = MyServerProtocol
	reactor.listenTCP(port, WebFactory)
	reactor.run()
	
	

