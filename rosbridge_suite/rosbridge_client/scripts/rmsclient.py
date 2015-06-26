#!/usr/bin/python

from subprocess import Popen

import rospy
import json

from rosauth.srv import Authentication

from signal import signal, SIGINT, SIG_DFL
from functools import partial

from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.websocket import WebSocketHandler

from rosbridge_library.rosbridge_protocol import RosbridgeProtocol
from twisted.internet import reactor

from autobahn.twisted.websocket import WebSocketClientProtocol, \
									   WebSocketClientFactory

import sys
from subprocess import Popen
import time

streamProcess = []
bridgeProcess = []

class MyClientProtocol(WebSocketClientProtocol):
	

	state = 0

	def onConnect(self, response):
		print("Server connected: {0}".format(response.peer))

	def onOpen(self):
		print("Start websocket connection to server.")
		
		#Registration robot - argv[1] - login, argv[2] - name
		self.Message = "REGISTRATION:ROBOT|" + str(sys.argv[1]) + "|" + sys.argv[2];
		self.sendMessage(self.Message.encode('utf8'))

	def onMessage(self, payload, isBinary):
		if isBinary:
			 print("Binary message received: {0} bytes".format(len(payload)))
		else:
			 print("Text message received: {0}".format(payload.decode('utf8')))
	
		
		#################################
		#			Protocol 			#
		#################################

		self.parseData = payload.split('|')
		
		if len(self.parseData) != 0:
			
			self.id = self.parseData[0].split(':')

			if self.id[0] == 'REGISTRATION':
				if self.id[1] == 'SERVER':
					if self.parseData[1] == 'OK':
						print 'ROBOT: REGISTRATION ROBOT OK'
					elif self.parseData[1] == 'FALSE':
						print 'ROBOT: REGISTRATION FALSE'

			if self.id[0] == 'SERVER':
				if self.id[1] == 'BRIDGECONNECTION':    
					self.bridge = Popen(['./rmsrosbrwebsock.py', self.parseData[1], str(sys.argv[1]), 'shell=True'])
					streamProcess.append(self.bridge)

				elif self.id[1] == 'STREAMCONNECTION':
					time.sleep(2)
					self.stream = Popen(['./client', '37.205.11.196', self.parseData[1], 'shell=True'])
					streamProcess.append(self.stream)





	def onClose(self, wasClean, code, reason):
			print("WebSocket connection closed: {0}".format(reason))


if __name__ == '__main__':

   import sys
   from twisted.python import log
   from twisted.internet import reactor

   log.startLogging(sys.stdout)

   factory = WebSocketClientFactory("ws://"+str(sys.argv[3])+":"+str(sys.argv[4]), debug = False)
   factory.protocol = MyClientProtocol

   reactor.connectTCP(str(sys.argv[3]), int(sys.argv[4]), factory)
   reactor.run()

