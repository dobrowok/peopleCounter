import os

class Contador:

    def __init__(self, logger):
        self.id = os.getpid()
        self.frame = None
        self._countFlag = os.getenv('COUNT')
        self.LOG = logger
        self.LOG.info('countFlag= ' +str(self._countFlag) )
        
        self._countUp = 0
        self._countDown = 0
        self._model = 'Basic OpenCV'
        self.LOG.info('Contador[%s] successfully loaded', self._model)   

    def stop(self):
        self._mustRun = False
    
    def getVersion(self):
        return 'ContadorFake 1.0'
    
    def getJson(self):
        Data =  {
                    'count_up':   'fake',
                    'count_down': 'fake',
                    'model':      'fake'
                }
                
    def run(self):
        pass
        
    