#
# Maintainer:   Cambus
# Version:      0.0.1
#
#

import os
import sys
import time
import threading
import logging
import numpy as np
import cv2
sys.path.insert(0, '../../') # Para poder importar o 'Pessoa' que esta 2 diretorios acima
sys.path.insert(0, './') # Para poder importar o 'Pessoa' que esta 2 diretorios abaixo
import Pessoa
import time
#from matplotlib import pyplot as plt
import math
import decimal
from random import randint

class Contador:

    def __init__(self, logger):
        self.id = os.getpid()
        self.frame = None
        self._countFlag = os.getenv('COUNT')
        self.LOG = logger
        self.LOG.info('countFlag= ' +str(self._countFlag) )
        
        self._countUp = 0
        self._countDown = 0
        self._model = 'Naive Trained'
        self.LOG.info('Contador[%s] successfully loaded', self._model)
        
    def getVersion(self):
        return 'ContadorFake 1.0'

    def stop(self):
        self._mustRun = False

    def run(self):
        self._mustRun = True
        
        # Roda dentro de uma thread
        if(self._countFlag):
            T1 = threading.Thread(target=self.detectPeople)
            T1.daemon = True    # Permite CTR+C parar o progama!
            T1.start()
        else:
            self._model = 'dummy'
            T2 = threading.Thread(target=self.detectPeopleSimulator)
            T2.daemon = True
            T2.start()
        
    def getJson(self):
        Data =  {
                    'count_up':   self._countUp,
                    'count_down': self._countDown,
                    'model':      self._model
                }

        return Data
        
    def detectPeopleSimulator(self):
        self.LOG.info('CounterThread= ' +str(threading.current_thread()) )
        while(self._mustRun):
            time.sleep( 2 )
            self._countUp = randint(0, 9)
            self._countDown = randint(0, 9)
        
    def detectPeople(self):

        #Contadore de entrada e saida
        self._countUp = 0
        self._countDown = 0

        self.frame = None
        # Fonte de video
        # cap = cv2.VideoCapture(0) # Descomente para usar a camera.
        # cap = cv2.VideoCapture("C:\\Users\\Bruno\\Documents\\GitHub\\Contador\\peopleCounter.avi") #Captura um video
        #self.cap = cv2.VideoCapture("C:\\Users\\Bruno\\Documents\\GitHub\\Contador\\d.mp4")  # Captura um video
        self.cap = cv2.VideoCapture("..\\..\\bus.avi") #Captura um video
        self.w = self.cap.get(3)
        self.h = self.cap.get(4)

        #Linhas de Entrada/Saida
        self.line_up = int(2*(self.h/4))    #deve-se adaptar de acordo com as caracteristicas da camera
        self.line_down = int(2*(self.h/4))  #deve-se adaptar de acordo com as caracteristicas da camera
        #self.line_up = int(2.25 * (self.h / 6))
        #self.line_down = int(3.75 * (self.h / 6))

        self.up_limit = int(1*(self.h/6))
        self.down_limit = int(5*(self.h/6))

        # Contadore de entrada e saida
        self.cnt_up = 0
        self.cnt_down = 0

        svm = cv2.ml.NormalBayesClassifier_create()
        try:
            svm = svm.load('ml/naiveB/svm_data1.dat')
        except:
            sys.path.insert(1, './ml/naiveB') # Para poder importar o 'Pessoa' que esta 2 diretorios acima
            svm = svm.load('svm_data1.dat')

        frameArea = self.h*self.w
        print("Area do Frame:", frameArea)
        areaTH = frameArea/225
        print ('Area Threshold', areaTH) # Area de contorno usada para detectar uma pessoa
        print ("Limite entrada:", self.line_up)
        print ("Limite saida:", self.line_down)
        print ("Limite superior:", self.up_limit)
        print ("Limite inferior:", self.down_limit)

        #Substrator de fundo
        fgbg = cv2.createBackgroundSubtractorMOG2(300, detectShadows=False)

        #Elementos estruturantes para filtros morfoogicos
        kernelOp = np.ones((3,3),np.uint8)
        kernelOp2 = np.ones((5,5),np.uint8)
        kernelOp3 = np.ones((8, 8), np.uint8)
        kernelCl = np.ones((11,11),np.uint8)
        kernelCl2 = np.ones((8, 8), np.uint8)

        #Inicializacao de variaveis Globais
        font = cv2.FONT_HERSHEY_SIMPLEX
        pessoas = []
        dictEntrada = {000: 000}
        dictSaida = {000: 000}
        max_p_age = 5
        pid = 1

        while self.cap.isOpened():
            ret, frame = self.cap.read()
            ## frame = image.array

            for pessoa in pessoas:
                pessoa.age_one()

            #Aplica subtracao de fundo
            fgmask = fgbg.apply(frame)
            fgmask2 = fgbg.apply(frame)

            #Binarizacao para eliminar sombras (color gris)
            try:

                fgmask = cv2.GaussianBlur(fgmask, (3, 3), 0)
                fgmask2 = cv2.GaussianBlur(fgmask2, (3, 3), 0)

                ret, imBin = cv2.threshold(fgmask, 128, 255, cv2.THRESH_BINARY)
                ret, imBin2 = cv2.threshold(fgmask2, 128, 255, cv2.THRESH_BINARY)
                #Opening (erode->dilate) para remover o ruido.
                mask = cv2.morphologyEx(imBin, cv2.MORPH_OPEN, kernelOp3)
                mask2 = cv2.morphologyEx(imBin2, cv2.MORPH_OPEN, kernelOp3)
                #Closing (dilate -> erode) para juntar regioes brancas.
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernelCl2)
                mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernelCl2)
            except:
                print('EOF')
                print('Entrou:', self.cnt_up)
                print('Saiu:', self.cnt_down)

            _, contours0, hierarchy = cv2.findContours(mask2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours0:
                area = cv2.contourArea(cnt)
                peri = cv2.arcLength(cnt, True)
                M = cv2.moments(cnt)

                if area > areaTH:

                    #M = cv2.moments(cnt)
                    cx = int(M['m10']/M['m00'])
                    cy = int(M['m01']/M['m00'])

                    x, y, w, h = cv2.boundingRect(cnt)

                    new = True
                    if cy in range(self.up_limit, self.down_limit):
                        shape = np.float32(cv2.HuMoments(M)).reshape(-1, 7)
                        predict = svm.predict(shape)[1]

                        for pessoa in pessoas:
                            if abs(cx - pessoa.getX()) <= w and abs(cy - pessoa.getY()) <= h:
                                # O objeto esta perto de um que ja foi detectado anteriormente
                                new = False
                                pessoa.updateCoords(cx, cy)   #atualizar coordenadas no objeto e reseta a idade
                                if pessoa.deslocaCima(self.line_down, self.line_up) and (str(predict) == "[[1]]" ):
                                    if dictEntrada.get(pessoa.getId()) != pessoa.getId():
                                        self.cnt_up += 1;
                                        print("-------------------------------------------------------------------------------------------------------")
                                        print("ID: ", pessoa.getId(), 'Entrou as', time.strftime("%c"))
                                        print("Area objeto: " + str(area))
                                        print("Perimetro: ", peri)
                                        print("Shape da pessoa: ", shape[0])

                                    dictEntrada[pessoa.getId()] = pessoa.getId()

                                elif pessoa.deslocaBaixo(self.line_down, self.line_up) and (str(predict) == "[[1]]" ):

                                    if dictSaida.get(pessoa.getId()) != pessoa.getId():
                                        self.cnt_down += 1;
                                        print("-------------------------------------------------------------------------------------------------------")
                                        print("ID: ", pessoa.getId(), 'Saiu as', time.strftime("%c"))
                                        print("Area objeto: " + str(area))
                                        print("Perimetro: ", peri)
                                        print("Shape da pessoa: ", shape[0])

                                    dictSaida[pessoa.getId()] = pessoa.getId()
                                break
                            if pessoa.getState() == '1':
                                if pessoa.getDir() == 'Saiu' and pessoa.getY() > down_limit:
                                    pessoa.setDone()
                                elif pessoa.getDir() == 'Entrou' and pessoa.getY() < up_limit:
                                    pessoa.setDone()

                            if pessoa.timedOut():
                                #remover pessoas da lista
                                index = pessoas.index(pessoa)
                                pessoas.pop(index)
                                #print(dictEntrada)
                                #print(dictSaida)

                                del pessoa #libera memoria
                        if new:
                            p = Pessoa.Pessoa(pid, cx, cy, max_p_age, time.time())
                            pessoas.append(p)
                            pid += 1
                    #################
                    #   DESENHOS    #
                    #################
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                    img = cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    #cv2.drawContours(frame, cnt, -1, (0,255,0), 3)

            #END for cnt in contours0

            #########################
            # DESENHAR TRAJETORIAS  #
            #########################
            for pessoa in pessoas:
                if len(pessoa.getTracks()) >= 2:
                   pts = np.array(pessoa.getTracks(), np.int32)
                   pts = pts.reshape((-1, 1, 2))
                   frame = cv2.polylines(frame, [pts], False, pessoa.getRGB())
                #if pessoa.getId() == 9:
                   #print (str(pessoa.getX()), ',', str(pessoa.getY()))
                cv2.putText(frame, str(pessoa.getId()), (pessoa.getX(), pessoa.getY()), font, 0.3, pessoa.getRGB(), 1, cv2.LINE_AA)

            self.escreveLinhasDePassagem(frame)

            self.escreveCabecalho(frame, font)

            cv2.imshow('Frame', frame)
            cv2.imshow('Debug', mask)

            #pressionar ESC para sair
            k = cv2.waitKey(30) & 0xff
            if k == 27:
                break
        #END while(cap.isOpened())

        #################
        #   LIMPEZA     #
        #################
        cap.release()
        cv2.destroyAllWindows()

    def escreveLinhasDePassagem(self, frame):

        #Propriedades das linhas
        line_down_color = (0, 0, 255)
        line_up_color = (255, 0, 0)

        pt1 = [0, self.line_down];
        pt2 = [self.w, self.line_down];

        pts_L1 = np.array([pt1, pt2], np.int32)
        pts_L1 = pts_L1.reshape((-1, 1, 2))

        pt3 = [0, self.line_up];
        pt4 = [self.w, self.line_up];

        pts_L2 = np.array([pt3, pt4], np.int32)
        pts_L2 = pts_L2.reshape((-1, 1, 2))

        pt5 = [0, self.up_limit];
        pt6 = [self.w, self.up_limit];

        pts_L3 = np.array([pt5,pt6], np.int32)
        pts_L3 = pts_L3.reshape((-1, 1, 2))

        pt7 = [0, self.down_limit];
        pt8 = [self.w, self.down_limit];

        pts_L4 = np.array([pt7, pt8], np.int32)
        pts_L4 = pts_L4.reshape((-1, 1, 2))

        frame = cv2.polylines(frame, [pts_L1], False, line_down_color, thickness=2)
        frame = cv2.polylines(frame, [pts_L2], False, line_up_color, thickness=2)
        frame = cv2.polylines(frame, [pts_L3], False, (255, 255, 255), thickness=1)
        frame = cv2.polylines(frame, [pts_L4], False, (255, 255, 255), thickness=1)

    def escreveCabecalho(self, frame, font):

        str_up = 'Entraram ' + str(self.cnt_up)
        str_down = 'Sairam ' + str(self.cnt_down)
        tituloup = "Entrada "
        titulodown = "Saida "
        dataehora = time.strftime("%c")

        cv2.putText(frame, str_up, (10, 40), font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, str_up, (10, 40), font, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(frame, str_down, (10, 60), font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, str_down, (10, 60), font, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, tituloup, (int(self.w/2), 20), font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, titulodown, (int(self.w/2), 450), font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, dataehora, (420, 20), font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)


if __name__ == '__main__':
    LOG = logging.getLogger(__name__)
    c = Contador(LOG)
    c.detectPeople()
