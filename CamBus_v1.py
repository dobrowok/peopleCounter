#
# Maintainer:   Cambus
# Version:      0.0.1
#
#

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 

import os
import sys
import time
import datetime
import threading
import platform
import logging
#from contextlib import suppress
import json
import imp
import urllib

print('Python Version=' +sys.version)
if sys.version_info[0] == 3:
    import http.client 
    import configparser
else:
    import httplib
    import ConfigParser 

from uuid import getnode as get_mac
from Contador_v1    import Contador
from Sensors_v1     import Sensors
from MqttClient_v1  import MQttClient

configFilename = "CamBus.ini"

# Este eh o modelo basico que o AWS precisa para criar um 'shadow'
AWSData = {"state":{"reported":{}}}
# Para publicar, tem que ser no topico abaixo:
#   $aws/things/Dobrowok/shadow/update

# Este eh o comando para pegar o shadow com CURL
#   curl --tlsv1.2 --cert ./e866e9eb47-certificate.pem.crt.txt --key ./e866e9eb47-private.pem.key --cacert ./aws-iot-rootCA.pem -X GET https://a3k400xgjmh5lk.iot.us-east-2.amazonaws.com:8443/things/Dobrowok/shadow


# Error values
CAMBUS_INVALID_MQ_TYPE = -12
CAMBUS_INVALID_SO = -13

LOG = logging.getLogger(__name__)

class CamBus:

    def __del__(self):
        #Publica mensagem indicando que caiu
        bData = AWSData
        bData['state']['reported']['BUS'] =           self.getJson()
        bData['state']['reported']['BUS']['Status'] = 'shut down'
        bData['state']['reported']['SENSORS'] =       'off-line'
        bData['state']['reported']['COUNTER'] =       'off-line'
        self._mqtt.publish(self._topic, json.dumps(bData) )
        self.publishDweet(json.dumps(bData) )
        self._sensor.blink('BLUE', 1)
        
        # Salva configuracoes mudadas
        self._lastShutdown = str(datetime.datetime.now())
        self.saveConfig()
        print ('CamBus[', self._PID, '] died')

    # Encontra o nome do sistema operacional (para pode carregar arquivos de hardware especificos)
    def getOS (self):   
        OS = platform.uname()
        
        if (OS[0] == 'Windows') or (OS[1] == 'vmlinux'):
            return 'Windows'

        elif OS[1] == 'raspberrypi':     # para a Raspberry PI
            return 'raspberrypi'

        elif OS[1] == 'linaro-alip':  # Para a Dragon
            return 'linaro-alip'
        
        else:
            # Do the default
            LOG.critical('Unknown operational system [' +OS[0] +',' +OS[1] +']')
            sys.exit(CAMBUS_INVALID_SO)

    def __init__(self):
        self.frame = None
        
        ########################################################################################
        # Dados basicos: sistema operacional, PID, e o MAC (para gerar um nome unico no MQTT)
        self._PID = os.getpid()
        self._ID = hex(get_mac())
        
        self.setLogger()
        self.readConfig()
        
        self._OS = self.getOS()
        self._sensor = Sensors(LOG, self._OS)
        
        py_mod = imp.load_source('Contador', self._busConfig.get('DEFAULT','contador_class'))

        if hasattr(py_mod, 'Contador'):
                self._counter = getattr(py_mod, 'Contador')(LOG)

        self._mqtt = MQttClient(LOG, self._OS, self._lastShutdown)
        self._subscribeTo = self._busConfig.get('MQTT','SUBSCRIBE_TO')
        self._topic =       self._busConfig.get('MQTT','BASE_TOPIC') ### +self._name +'/' + self._car
      
        LOG.info('CamBus[%s] successfully started for Python %d.%d', self._OS, sys.version_info[0], sys.version_info[1])    

    def setLogger(self):
        ########################################################################################
        # Sistema de log: pega da variavel de ambiente LOGLEVEL
            #LOG.debug('debug message')
            #LOG.info('info message')
            #LOG.warn('warn message')
            #LOG.error('error message')
            #LOG.critical('critical message')

        logging.basicConfig(level=logging.INFO)
        #LOG = logging.getLogger(__name__)
        
        if os.getenv('LOGLEVEL') == 'ERROR':
            LOG.setLevel(logging.ERROR)        
        elif os.getenv('LOGLEVEL') == 'DEBUG':
            LOG.setLevel(logging.DEBUG)        
        else:
            LOG.setLevel(logging.INFO)      

        # create a file handler
        handler = logging.FileHandler('CamBus.log')
        handler.setLevel(logging.INFO)

        # create a logging format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        # add the handlers to the logger
        LOG.addHandler(handler)

    ########################################################################################
    # Salva parametros atuais        
    def saveConfig(self):
        # Update timestamp
        ts = str(time.time() )
        agora = str(datetime.datetime.now())        
        
        #with suppress(Exception):
        cfgFile = open(configFilename, 'w')            
        ###self.config = configparser.ConfigParser()
        self._busConfig.set('DEFAULT', 'LAST_TIMESTAMP', ts)
        self._busConfig.set('DEFAULT', 'LAST_SHUTDOWN',  agora)
            
        self._busConfig.set('MQTT', 'mq',   self._mq)
        self._busConfig.set('MQTT', 'host', self._host)
        self._busConfig.set('MQTT', 'port', self._port)
        
        self._busConfig.write(cfgFile)
        cfgFile.close()
        
    # Tenta ler, se nao existir cria com o valor default passado como argumento
    def configSetDefault(self, section, key, value):
        try:
            self._busConfig.get(section,key)

        except:
            self.addSectionNoException(self._busConfig, section)
            self._busConfig.set(section, key, value)
        
    def addSectionNoException(self, config, section):
        try:
            config.add_section(section)
        except:
            pass
        
    ########################################################################################
    # Le dados de configuracao e ultimo timestamp valido
    def readConfig(self):
        if sys.version_info[0] == 3:
            self._busConfig = configparser.ConfigParser()
        else:
            self._busConfig = ConfigParser.ConfigParser()
            
        self._busConfig.read(configFilename)
        cfgfile = open(configFilename, 'r')
        
        # Sessoes default
        self.addSectionNoException(self._busConfig, 'MQTT')
        self.addSectionNoException(self._busConfig, 'MQTT_eclipse')
        self.addSectionNoException(self._busConfig, 'MQTT_local')
        self.addSectionNoException(self._busConfig, 'MQTT_aws')
        self.addSectionNoException(self._busConfig, 'BUS')
        self.addSectionNoException(self._busConfig, 'SENSORS')
        self.configSetDefault('DEFAULT', 'Contador_class', 'Contador_v1')
        self.configSetDefault('DEFAULT', 'Sensors_class', 'Sensors_v1')
        
        # valores default
        self.configSetDefault('MQTT', 'mq', 'aws')
        self.configSetDefault('MQTT', 'host', 'a3k400xgjmh5lk.iot.us-east-2.amazonaws.com')
        self.configSetDefault('MQTT', 'port', '8883')
        self.configSetDefault('MQTT', 'base_topic',   '$aws/things/Dobrowok/shadow/update')
        self.configSetDefault('MQTT', 'subscribe_to', 'aws/command/#')
        
        self.configSetDefault('MQTT', 'clientId', 'Teste')
        self.configSetDefault('MQTT', 'thingName', 'Teste')
        self.configSetDefault('MQTT', 'caPath', 'aws-iot-rootCA.pem')
        self.configSetDefault('MQTT', 'certPath', 'e866e9eb47-certificate.pem.crt.txt')
        self.configSetDefault('MQTT', 'keyPath', 'e866e9eb47-private.pem.key')
        self.configSetDefault('MQTT', 'publish_interval', '5')

        
        self.configSetDefault('MQTT_eclipse', 'mq', 'eclipse')
        self.configSetDefault('MQTT_eclipse', 'host', 'm2m.eclipse.org')
        self.configSetDefault('MQTT_eclipse', 'port', '1883')
        
        self.configSetDefault('MQTT_local', 'mq', 'mqtt')
        self.configSetDefault('MQTT_local', 'host', 'localhost')
        self.configSetDefault('MQTT_local', 'port', '1883')
        
        self.configSetDefault('MQTT_aws', 'mq', 'aws')
        self.configSetDefault('MQTT_aws', 'host', 'a3k400xgjmh5lk.iot.us-east-2.amazonaws.com')
        self.configSetDefault('MQTT_aws', 'port', '8883')
        
        self.configSetDefault('BUS', 'name', 'Vila Cruzeiro')
        self.configSetDefault('BUS', 'car', '11234')
        self.configSetDefault('BUS', 'line', '6422-10')
        self.configSetDefault('BUS', 'status', 'moving')
        
        self.configSetDefault('SENSORS', 'timestamp',  '2018-09-15 09:16:57.977719')
        self.configSetDefault('SENSORS', 'people_in',  '20')
        self.configSetDefault('SENSORS', 'people_out', '22')
        self.configSetDefault('SENSORS', 'temp',       '24.1')
        self.configSetDefault('SENSORS', 'co2',        '99.9')
        self.configSetDefault('SENSORS', 'pressure',   '99.9')
        self.configSetDefault('SENSORS', 'gps',        '20.34')
        self.configSetDefault('SENSORS', 'rain',       'true')
        self.configSetDefault('SENSORS', 'weight',     '12t')
        
       
        #Cria valores default falsos
        self._lastShutdown = '???'
        
        try:
            self._lastShutdown = self._busConfig.get('DEFAULT','LAST_SHUTDOWN')
        except:
            pass
         
        
        # Le os valores existentes para variaveis locais
        self._name =  self._busConfig.get('BUS','name')
        self._car  =  self._busConfig.get('BUS','car')
        self._line =  self._busConfig.get('BUS','line')

        self._mq =       self._busConfig.get('MQTT','mq')
        self._host =     self._busConfig.get('MQTT','host') 
        self._port =     self._busConfig.get('MQTT','port') 
        self._caPath =   self._busConfig.get('MQTT','caPath')
        self._certPath = self._busConfig.get('MQTT','certPath')
        self._keyPath =  self._busConfig.get('MQTT','keyPath')
        self._publishInterval = int(self._busConfig.get('MQTT','publish_interval'))

        agora = str(datetime.datetime.now())
        LOG.info('Starting now: [%s]', agora)
        LOG.info('Last shutdown was: [%s]', self._lastShutdown)
   
    def getJson(self):
        Data = {
                'Name': self._name,
                'Car':  self._car,
                'Line': self._line,
                'Status': 'dummy',
                'Last_timestamp': self._lastShutdown,
                'System': self._OS,
                'ID': self._ID
                }
        return Data
        
    def connectMQTT(self):
    
        bData = AWSData
        bData['state']['reported']['BUS'] =           self.getJson()
        bData['state']['reported']['BUS']['Status'] = 'start up'
        bData['state']['reported']['SENSORS'] =       'off-line'
        bData['state']['reported']['COUNTER'] =       'off-line'

        if  self._mq == 'fake':
            self._mqtt.setupFake()

        elif self._mq == 'mqtt'  or  self._busConfig.get('MQTT','MQ') == 'eclipse':
            self._mqtt.setup(self._host, self._port)
            self._mqtt.connect(self._topic, self._subscribeTo, bData)
            
        elif self._mq == 'eclipse':
            self._mqtt.setup(self._host, self._port)
            self._mqtt.connect(self.topic, self._subscribeTo, bData)
            
        elif self._mq == 'aws':
            self._mqtt.setup(self._host, self._port)
            self._mqtt.AWSConnect(self._caPath, self._certPath,  self._keyPath, self._topic, self._subscribeTo, bData )

        else:
            LOG.critical('[MQ] = ' +self._mq +', is an invalid option!')
            sys.exit(CAMBUS_INVALID_MQ_TYPE)

    # Carrega um novo modeo (objeto) de um arquivo PY que chegou pelo MQtt
    def loadFile(self):
        if self._mqtt._filename is not '':
            LOG.critical('Loading = [' +self._mqtt._filename +']')
            
            mod_name,file_ext = os.path.splitext(self._mqtt._filename)

            if file_ext.lower() == '.py':
                py_mod = imp.load_source(mod_name, self._mqtt._filename)

            elif file_ext.lower() == '.pyc':
                py_mod = imp.load_compiled(mod_name, self._mqtt._filename)

            if hasattr(py_mod, 'Contador'):
                self._counter = getattr(py_mod, 'Contador')(LOG)

            # Limpa
            self._mqtt._filename = ''
            LOG.warning('Loaded version = [' +self._counter.getVersion() +']')
            self._counter.stop()
            self._counter.run()

    def publishDweet(self, json_string):
        '''
        try:
            import ssl
        except ImportError:
            print "error: no ssl support"
        ''' 
        hdr = {"content-type": "application/json"}

        try:
            if sys.version_info[0] == 3:
                #import http.client 
                conn = http.client.HTTPSConnection('dweet.io')
            else:
                conn = httplib.HTTPConnection('dweet.io')

            conn.request('POST', '/dweet/for/Dobrowok', json_string, hdr)
            response = conn.getresponse()
            #r2 = response.read() # same as r.text in 3.x
            if(response.status != 200):
                LOG.error('Dweet error: [%d] %s', response.status, response.reason)
                
            conn.close()
            LOG.info('publishDweet(dweet.io, ' +json_string[0:35] +'  ...})')
            
        except Exception as inst:
            LOG.error('Dweet error: %s', inst)
            conn.close()
        
        except KeyboardInterrupt:
            raise
       
    def runCamBus(self):
        #print('logLevel= ' +str(logging.getLogger().getEffectiveLevel()) )
        LOG.info('PID=  ' +str(self._PID) ) 
        LOG.info('ID=   ' +self._ID)
        LOG.info('mq=   ' +self._mq)
        LOG.info('MainThread= ' +str(threading.current_thread()) )
        
        self.connectMQTT()
        
        cData = AWSData
        cData['state']['reported']['BUS'] =           self.getJson()
        cData['state']['reported']['BUS']['Status'] = 'running'
        cData['state']['reported']['SENSORS'] =       self._sensor.getJson()
        cData['state']['reported']['COUNTER'] =       self._counter.getJson()
        
        self.publishDweet(json.dumps(cData) )

        # Infinite loops, in threads
        self._mqtt.run() 
        self._counter.run()
       
        while True:
            # Loop principal do programa
            try:
                time.sleep( self._publishInterval )
            except:
                LOG.info('Finishing due to CTR+C')
                sys.exit(0)
            
            bData = AWSData
            
            bData['state']['reported']['BUS'] =           self.getJson()
            bData['state']['reported']['BUS']['Status'] = 'running'
            bData['state']['reported']['SENSORS'] =       self._sensor.getJson()
            bData['state']['reported']['COUNTER'] =       self._counter.getJson()
            
            
            self._mqtt.publish(self._topic, json.dumps(bData) )
            self.publishDweet(json.dumps(bData) )
            self._sensor.blink('BLUE', 1)
            
            self.loadFile()
        
        if(self._countFlag):
            Contador().detectPeople()
        else:
            print('please use export COUNT=x to enable Counting Process')
        
       

if __name__ == '__main__':
    CamBus().runCamBus()
    