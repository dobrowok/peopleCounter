#
# Maintainer:   Cambus
# Version:      0.0.1
#
#

import os
import paho.mqtt.client as paho
import socket
import ssl
import sys
import threading
from time import sleep
from random import uniform
import json

# Error values
MQTT_HOST_EMPTY = -31
MQTT_PORT_EMPTY = -32
MQTT_CONNECT_ERR = -33


class MQttClient:
    def __del__(self):
        print ('MQtt client[] died')

    def __init__(self, logger, OS, lastTimestamp):
        self._frame = None
        self.LOG = logger
        self._OS = OS
        self._lastTimestamp = lastTimestamp
        self._connFlag = False
        self._host = ''
        self._port = ''
        self._filename = ''
        self._fakeFlag = False
        
        self._mq = paho.Client()
        self._mq.on_connect = self.onConnect
        self._mq.on_message = self.onMessage
        self._mq.on_disconnect = self.onDisconnect
        
        self.LOG.info('MQtt[%s] successfully loaded', self._OS)

        #mq.on_log = on_log

    def run(self):
        # Roda dentro de uma thread
        T1 = threading.Thread(target=self.loop)
        T1.daemon = True    # Permite CTR+C parar o progama!
        T1.start()
        
    def loop(self):
        self.LOG.info('MQTTThread= ' +str(threading.current_thread()) )
        self._mq.loop_forever()

    def setupFake(self):
        self._fakeFlag = True
    
    def setup(self, host, port):
        self._host = host
        self._port = port
        
    def publish(self, topic, json_string):
        print('publish(' +self._host +')  ' +topic +', \n' +json_string)
        self._mq.publish(topic, json_string, qos=1)
    
    def connect(self, topic, subscribe_to, jSon):
    
        self._subscribeTo = subscribe_to
        if self._fakeFlag == True:
            return
            
        if (not self._host) or (self._host == ""):
            self.LOG.critical('[Host] cannot be empty! Use .setup() first')
            sys.exit(MQTT_HOST_EMPTY)
            
        elif (not self._port) or (self._host == ""):
            self.LOG.critical('[Port] cannot be empty! Use .setup() first')
            sys.exit(MQTT_PORT_EMPTY)
        
        try:
            self._mq.connect(self._host, int(self._port), keepalive=60)
          
        except (IOError, RuntimeError):
            self.LOG.critical('MQTT failed to connect to [' +self._host +':' +self._port +']')
            sys.exit(MQTT_CONNECT_ERR)
            
        self.LOG.debug('self._mq.publish(' +topic +', ' +json.dumps(jSon) +', qos=0)')
        self.doSubscribe(subscribe_to +'/command/#')
        self.doSubscribe(subscribe_to +'/file/#')
        
        # Publica uma mensagem inicial, para anunciar que comecou a enviar dados
        self._mq.publish(topic, json.dumps(jSon), qos=0)
    
    def AWSConnect(self, caPath, certPath, keyPath, topic, subscribeTo, jsonString):
        self._mq.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
        self.connect(topic, subscribeTo, jsonString)
    
    def doSubscribe(self, subscribeTo):
        print(self._mq.subscribe(subscribeTo))
        self.LOG.info('Subscribed to [' +subscribeTo +']')
    
    def onConnect(self, client, userdata, flags, rc):
        global _connFlag
        self._connFlag = True

        if rc==0:
            self.LOG.info('MQTT connected to [' +self._host +':' +self._port +']')
        else:
            self.LOG.error('MQTT error [' +rc +' when connecting to [' +self._host +':' +self._port +']')
            pass #todo 
            # 0: Connection successful 1: Connection refused - incorrect protocol version 2: Connection refused - invalid client identifier 3: Connection refused - server unavailable 4: Connection refused - bad username or password 5: Connection refused

    def onMessage(self, client, userdata, msg):
        
        Topic = str(msg.topic)
       
        # Recebeu um arquivo e tem que salvar
        if Topic.find('file') > 1:
            self._filename = os.path.basename(Topic)
            self.LOG.info('Received a file: [' +self._filename +'] ')
            fout = open(self._filename,"wb")
            fout.write(msg.payload)
            fout.close()
            self.LOG.info('Saved file: [' +self._filename +']')
            
        else:
            self.LOG.info('Received a command: [' +Topic +']= ' +str(msg.payload))

        
    def onDisconnect(self, client, userdata, rc):
        if rc != 0:
            self.LOG.info('MQTT was disconnected from [' +self._host +':' +self._port +'] with error [' +str(rc) +']')
            # ToDo: reconectar????

        else:
            self.LOG.error('MQTT connection was forcibly closed by the remote host [' +rc +']')
    
    #def on_log(client, userdata, level, buf):
    #    print(msg.topic+" "+str(msg.payload))


