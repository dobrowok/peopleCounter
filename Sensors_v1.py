#
# Maintainer:   Cambus
# Version:      0.0.1
#
#

import os
import sys 
import time
import logging
import datetime
import platform
import threading
import subprocess

# Error values
SENSOR_CANNOT_IMPORT_GPIO = -21
SENSOR_UNKNOWN_SO =         -22
SENSOR_GPS_ERROR =          -23
SENSOR_RFID_ERROR =         -24

TAGS = {
        '67:6F:B7:73:CC': 'Motorista Vinicius',
        'A9:4F:B5:DD:8E': 'Motorista Kleber',
       }

class RFIDReader:
    
    def __init__(self, logger, blink, OS):
        self.LOG = logger
        self._blink = blink
        self._OS = OS
        
        
        # Roda dentro de uma thread
        T1 = threading.Thread(target=self.loop)
        T1.daemon = True    # Permite CTR+C parar o progama!
        T1.start()
        
    def loop(self):
         
        self.LOG.info('RFID= ' +str(threading.current_thread()) )
        if self._OS == 'raspberrypi':
            try:
                import MFRC522   # For RFID
                
                rfid = MFRC522.MFRC522()  # starting 
             
                while True:
                    # is there a tag around?
                    status, tag_type = rfid.MFRC522_Request(rfid.PICC_REQIDL)
             
                    if status == rfid.MI_OK:
             
                        # read the UID
                        status, uid = rfid.MFRC522_Anticoll()
             
                        if status == rfid.MI_OK:
                            uid = ':'.join(['%X' % x for x in uid])
                            self.LOG.info('UID= ' +uid )
             
                            # Verifiy identity
                            if uid in TAGS:
                                self.LOG.info('Benvindo ' +TAGS[uid] )
                                self._blink.blink('PURPLE', 2)

                            else:
                                self.LOG.warn('Tag nao reconhecido! [' +str(uid) +']' )
                                self._blink.blink('RED', 2)
            
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                GPIO.cleanup()
                self.LOG.critical('RFID  exception')
                sys.exit(SENSOR_RFID_ERROR)

    
class GPS:
    def __init__(self, logger, OS):
        import gps

        self.LOG = logger
        self._OS = OS
        self._gpsReport = ''
        
        # Listen on port 2947 (gpsd) of localhost
        for i in range(0,3):   # permite retry de 4 vezes em caso de erro de GPS

            try:
                self._session = gps.gps("localhost", "2947")
                self._session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
                
            except Exception as e:              
                if 'Cannot assign requested address' in str(e):
                    # Consigo recuperar, ligando o GPS
                    self.LOG.warning('GPS initialization error [' +str(e) +']. Will try to start it...')
                    if self._OS == 'raspberrypi':     # para a Raspberry PI
                        return_code = subprocess.call("sudo gpsd /dev/ttyS0 -F /var/run/gpsd.sock  # Liga o deamon", shell=True) 
                        
                    continue
                    
                else:
                    self.LOG.critical('GPS initialization final error [' +str(e) +']')
                    sys.exit(SENSOR_GPS_ERROR)
            
            break  # Se deu tudo erto, ja sai
            
        if(i >= 3):
            # nao deu certo mesmo! sai com erro
            self.LOG.critical('GPS initialization error')
            print('Servico down. Use: \n sudo gpsd /dev/ttyS0 -F /var/run/gpsd.sock  # Liga o deamon')
            sys.exit(SENSOR_GPS_ERROR)
              
        # Roda dentro de uma thread
        T1 = threading.Thread(target=self.loop)
        T1.daemon = True    # Permite CTR+C parar o progama!
        T1.start()
    
    def loop(self):
        self.LOG.info('GPS= ' +str(threading.current_thread()) )
     
        while True:
            try:
                report = self._session.next()
                # Wait for a 'TPV' report and display the current time
                # To see all report data, uncomment the line below
                # print(report)
                if report['class'] == 'TPV':
                    if hasattr(report, 'time'):
                        self._gpsReport = report
                        #print(self._gpsReport )
                        #print('lon=' +str(report.lon) +'; lat=' +str(report.lat) )
                
                time.sleep(1)
                
            except KeyError:
                pass
                
            except KeyboardInterrupt:
                self.LOG.critical('GPS KeyboardInterrupt exception')
                sys.exit(SENSOR_GPS_ERROR)

            except StopIteration:
                self._session = None
                self.LOG.critical('GPSD has terminated')
                sys.exit(SENSOR_GPS_ERROR)
    
    def getJson(self):
        if (self._gpsReport == ''):
            Data = 'not available'
        
        else:
            try:
                Data = {
                            'lon':   self._gpsReport.lon, 
                            'lat':   self._gpsReport.lat,
                            'alt':   self._gpsReport.alt,
                            'speed': self._gpsReport.speed
                        }        
            except:
                Data = 'error getting values'           

        return Data
    

class Sensors:
    def __del__(self):
        if hasattr(self, 'GPIO'):
            self.GPIO.cleanup()
            
        print ('Sensor[] died')

    def __init__(self, logger, so):
        self.frame = None
       
        self.LOG = logger
        self._OS = so
        
        # Tenta importar a biblioteca GPIO correta para o hardware
        try:
            if (self._OS == 'Windows') or (self._OS == 'vmlinux') :
                # Fake GPIO
                #self.GPIO = '{ fake}' 
                pass
                
            elif self._OS == 'raspberrypi':     # para a Raspberry PI
                import RPi.GPIO as gpio
                
                #Configuring GPIO 
                gpio.setwarnings(False)
                gpio.setmode(gpio.BOARD)
                gpio.setup(38,gpio.OUT)  # Led vermelho
                gpio.setup(40,gpio.OUT)  # Led azul
                 
                #Configuring GPIO as PWM (frequency 20 Hz)
                self._pwmRed = gpio.PWM(38,20)
                self._pwmBlue = gpio.PWM(40,20)

                #Initializing PWM
                self._pwmBlue.start(0)
                self._pwmRed.start(0)
                
                self._gps = GPS(logger, self._OS)
                self._rfid = RFIDReader(logger, self, self._OS)
                
            elif self._OS == 'linaro-alip':  # Para a Dragon
                from GPIOLibrary import GPIOProcessor

                self.GPIO = GPIOProcessor()
                self._gps = GPS(logger, self._OS)
                self._rfid = RFIDReader(logger, self, self._OS)

            else:
                # Do the default
                self.LOG.critical('Unknown operational system [' +self._OS +']')
                sys.exit(SENSOR_UNKNOWN_SO)
            
        except RuntimeError:
            self.LOG.critical('Error importing GPIO for system [%s]!  This is probably because you need superuser privileges.  You can achieve this by using [sudo] to run your script', self.OS)
            sys.exit(SENSOR_CANNOT_IMPORT_GPIO)
        
         # Default value 
        self._Temp = 23
        
        # sucesso
        self.LOG.info('Sensors[%s] successfully loaded', self._OS)

    def cat(self, filename):
        try:
            with open(filename) as f:
                for line in f:
                    return line
                    
        except IOError as e:
            self.LOG.error('I/O error[%s]: %s',  filename, str(e.strerror))
            return('I/O error!')
            
    def blink(self, colour, delay):
        self.LOG.debug(':blink(colour=' +colour +', delay=' +str(delay) +'):')
        if (self._OS == 'Windows') or (self._OS == 'vmlinux') or (self._OS == 'linaro-alip') :
            print(colour)
            return
            
        elif self._OS == 'raspberrypi':
            if colour=='RED':
                self._pwmRed.ChangeDutyCycle(1)
                
            elif colour=='BLUE':
                self._pwmBlue.ChangeDutyCycle(1)
            
            elif colour=='PURPLE':
                self._pwmRed.ChangeDutyCycle(1)
                self._pwmBlue.ChangeDutyCycle(1)
                
        time.sleep(delay)
        self._pwmBlue.ChangeDutyCycle(0)
        self._pwmRed.ChangeDutyCycle(0)
    
    # Return CPU temperature as a character string                               
    def getRaspCPUTemperature(self):
        res = os.popen('vcgencmd measure_temp').readline()
        return (res.replace("temp=","").replace("'C\n",""))


    def getJson(self):
        self.LOG.debug('getSensorValues(' +self._OS +')')
        
        if self._OS == 'Windows':
            self._Temp += 1

            Data =  [
                        {   
                            'gps': 'not available'
                        } ,
                        {
                            'name': 'Temp',
                            'type': 'centigrade',
                            'value':  self._Temp
                        } , 
                        {
                            'name': 'CO2',
                            'type': 'ppm',
                            'value': self._Temp
                        }
                    ]
                    
        elif self._OS == 'raspberrypi':
            Data = [
                    {   
                        'gps': self._gps.getJson() 
                    } ,
                    {
                        'name': 'CPUTemp',
                        'type': 'centigrade',
                        'value':  self.getRaspCPUTemperature()
                    } , 
                    {
                        'name': 'CO2',
                        'type': 'ppm',
                        'value': self._Temp
                    }
                ]

        elif self._OS == 'linaro-alip':
            Data = [
                   {
                        'gps': self._gps.getJson() 
                    } ,
                    {
                        'name': 'CPUTemp',
                        'type': 'centigrade',
                        'value':  float(self.cat('/sys/class/thermal/thermal_zone0/temp')) / 1000.0
                    }
                   ]

        else:
            # Do the default
            self.LOG.critical('Unknown operational system [' +self._OS +']')
            sys.exit(SENSOR_UNKNOWN_SO)
         
        #Data['GPS'] = 'bla'
        return Data

 
 
if __name__ == '__main__':
    LOG = logging.getLogger(__name__)
    handler = logging.FileHandler('CamBus.log')
    LOG.addHandler(handler)
    
    print(platform.system())
    #try:
    Sensors(LOG).getSensorValues()
    #except:
    #    pass
     
