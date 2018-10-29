#
# Maintainer:   Cambus
# Version:      0.0.1
#
#
# -*- coding: utf-8 -*-

import numpy as np
import cv2
import Pessoa
import time
from time import gmtime, strftime
import matplotlib 
import math
import decimal


class Contador:

    def __init__(self):
        self.frame = None

    def detectPeople(self):

        _center = [314.67404, 231.52438]
        #_center = [112.0679, 132.63786]
        list = []
        list_P = []
        list_N = []
        svm = cv2.ml.NormalBayesClassifier_create()
        #svm.setKernel(cv2.ml.SVM_LINEAR)
        #svm.setType(cv2.ml.SVM_C_SVC)
        #svm.setC(2.67)
        #svm.setGamma(5.383)

        #Contadore de entrada e saida
        cnt_up = 0
        cnt_down = 0

        #Fonte de video
        #cap = cv2.VideoCapture(0) # Descomente para usar a camera.
        #cap = cv2.VideoCapture("C:\\Users\\Bruno\\Documents\\GitHub\\Contador\\peopleCounter.avi") #Captura um video
        #cap = cv2.VideoCapture("C:\\Users\\Bruno\\Documents\\GitHub\\Contador\\d.mp4") #Captura um video
        #cap = cv2.VideoCapture("/home/vino/Documents/Contest2018/Cambus/contadorPessoas/src/videos/input2.avi") #Captura um video
        #cap = cv2.VideoCapture("/home/vino/Documents/Contest2018/Cambus/contadorPessoas/src/videos/cambus.avi")
        #cap = cv2.VideoCapture("/home/vino/Documents/Contest2018/Cambus/contadorPessoas/src/videos/sample-video.avi")
        cap = cv2.VideoCapture("..\\..\\bus.avi") #Captura um video

        #Descomente para imprimir as propriedades do video
        """for i in range(19):
            print (i, cap.get(i))"""

        #Metodo GET para pegar width e height do frame
        w = cap.get(3)
        h = cap.get(4)

        x_meio = int(w/2)
        y_meio = int(h/2)

        frameArea = h*w
        print("Area do Frame:", frameArea)
        areaTH = frameArea/50
        print ('Area Threshold', areaTH) # Area de contorno usada para detectar uma pessoa

        #Linhas de Entrada/Saida

        #line_up = int(2*(h/6))
        #line_down   = int(3*(h/6))
        line_up = int(4.7*(h/10))    #deve-se adaptar de acordo com as caracteristicas da camera
        line_down = int(5.3*(h/10))  #deve-se adaptar de acordo com as caracteristicas da camera
        print ("Line UP:", line_up)
        print ("Line DOW:", line_down)

        #up_limit =   int(1*(h/6))
        #down_limit = int(5*(h/6))
        up_limit =   int(0.1*(h/10))
        down_limit = int(9.9*(h/10))

        l1UP =   int(4.8*(h/10))
        l1DOWN = int(5.2*(h/10))
        l2UP =   int(4.9*(h/10))
        l2DOWN = int(5.1*(h/10))

        print ("Limite superior:", up_limit)
        print ("Limite inferior:", down_limit)

        #Propriedades das linhas

        print ("Red line y:",str(line_down))
        print ("Blue line y:", str(line_up))
        line_down_color = (0,0,255)
        line_up_color = (255,0,0)
        pt1 =  [0, line_down];
        pt2 =  [w, line_down];
        pts_L1 = np.array([pt1,pt2], np.int32)
        pts_L1 = pts_L1.reshape((-1,1,2))
        pt3 =  [0, line_up];
        pt4 =  [w, line_up];
        pts_L2 = np.array([pt3,pt4], np.int32)
        pts_L2 = pts_L2.reshape((-1,1,2))

        pt5 =  [0, up_limit];
        pt6 =  [w, up_limit];
        pts_L3 = np.array([pt5,pt6], np.int32)
        pts_L3 = pts_L3.reshape((-1,1,2))
        pt7 =  [0, down_limit];
        pt8 =  [w, down_limit];
        pts_L4 = np.array([pt7,pt8], np.int32)
        pts_L4 = pts_L4.reshape((-1,1,2))

        pt9 =  [0, l1UP];
        pt10 =  [w, l1UP];
        pts_L5 = np.array([pt9,pt10], np.int32)
        pts_L5 = pts_L5.reshape((-1,1,2))

        pt11 =  [0, l1DOWN];
        pt12 =  [w, l1DOWN];
        pts_L6 = np.array([pt11,pt12], np.int32)
        pts_L6 = pts_L6.reshape((-1,1,2))

        pt13 =  [0, l2UP];
        pt14 =  [w, l2UP];
        pts_L7 = np.array([pt13,pt14], np.int32)
        pts_L7 = pts_L7.reshape((-1,1,2))


        pt15 =  [0, l2DOWN];
        pt16 =  [w, l2DOWN];
        pts_L8 = np.array([pt15,pt16], np.int32)
        pts_L8 = pts_L8.reshape((-1,1,2))

        #Substrator de fundo
        #fgbg = cv2.createBackgroundSubtractorMOG2(detectShadows = False)
        #fgbg = cv2.createBackgroundSubtractorMOG2(500,detectShadows = True)
        fgbg = cv2.createBackgroundSubtractorMOG2()
        fgbg = cv2.createBackgroundSubtractorMOG()
        #fgbg = cv2.bgsegm.createBackgroundSubtractorMOG()
        #fgbg =  cv2.BackgroundSubtractorMOG()

        #kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3))
        #fgbg = cv2.bgsegm.createBackgroundSubtractorGMG()

        #Elementos estruturantes para filtros morfoogicos
        kernelOp = np.ones((3,3),np.uint8)
        kernelOp2 = np.ones((5,5),np.uint8)
        kernelOp3 = np.ones((8, 8), np.uint8)
        kernelCl = np.ones((11,11),np.uint8)
        kernelCl2 = np.ones((8, 8), np.uint8)

        #Inicializacao de variaveis Globais
        font = cv2.FONT_HERSHEY_SIMPLEX
        pessoas = []
        max_p_age = 5
        pid = 1

        while(cap.isOpened()):
            ##for image in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            #Le uma imagem de uma fonte de video

            ret, frame = cap.read()
            ## frame = image.array

            for pessoa in pessoas:
                pessoa.age_one() #age every person one frame
            #########################
            #   PRE-PROCESSAMENTO   #
            #########################

            #Aplica subtracao de fundo
            fgmask = fgbg.apply(frame)
            fgmask2 = fgbg.apply(frame)

            #Binarizacao para eliminar sombras (color gris)
            try:

                fgmask = cv2.GaussianBlur(fgmask, (3, 3), 0)
                #fgmask2 = cv2.GaussianBlur(fgmask2, (3, 3), 0)

                ret,imBin= cv2.threshold(fgmask,128,255,cv2.THRESH_BINARY)
                #ret,imBin2 = cv2.threshold(fgmask2,128,255,cv2.THRESH_BINARY)

                #Opening (erode->dilate) para remover o ruido.
                mask = cv2.morphologyEx(imBin, cv2.MORPH_OPEN, kernelOp)
                #mask2 = cv2.morphologyEx(imBin2, cv2.MORPH_OPEN, kernelOp)

                #Closing (dilate -> erode) para juntar regioes brancas.
                mask =  cv2.morphologyEx(mask , cv2.MORPH_CLOSE, kernelCl)
                #mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernelCl)
            except:
                print('EOF')
                print ('Entrou:',cnt_up)
                print ('Saiu:',cnt_down)

                #print(list)

                #a = np.array(list)
                Z = np.vstack(list)
                #Z = np.vstack(list)
                # convert to np.float32
                Z = np.float32(Z)

                # define criteria and apply kmeans()
                criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
                ret, label, center = cv2.kmeans(Z, 1, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

                # Now separate the data, Note the flatten()
                A = Z[label.ravel() == 0]
                B = Z[label.ravel() == 1]

                #print("A")
                #print(A)
                #print(len(A))
                #print("B")
                #print(B)
                #print(len(B))
                #print("centre ----")
               ## print(center)

                # Plot the data
                plt.scatter(A[:, 0], A[:, 1])
                plt.scatter(B[:, 0], B[:, 1], c='r')
                plt.scatter(center[:, 0], center[:, 1], s=80, c='y', marker='s')
                plt.xlabel('Height'), plt.ylabel('Weight')
                plt.show()
                a = np.float32(list_P)
                responses = np.array(list_N)
                #responses = np.float32(responses)
                print(len(a))
                print(len(responses))
                trained = svm.train(a, cv2.ml.ROW_SAMPLE, responses)
                if (trained):
                    print("trained", trained)
                    print("IsTrained", svm.isTrained())
                    svm.save('svm_data1.dat')

                else:
                    print("nao saolvou")

                #return (cnt_up - cnt_down)
                #break
            #################
            #   CONTORNOS   #
            #################

            # RETR_EXTERNAL returns only extreme outer flags. All child contours are left behind.
            _, contours0, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours0:
                #frame = cv2.drawContours(frame, cnt, -1, (0,255,0), 3, 8)
                area = cv2.contourArea(cnt)
                peri = cv2.arcLength(cnt, True)
                M = cv2.moments(cnt)
                ####
                #### coloca numa lista para treinamento 1
                list_P.append(np.float32(cv2.HuMoments(M)))
                list_N.append(0)
                ###

                ####
                #### coloca numa lista para treinamento 2
                #list_P.append(np.float32(cnt.flatten()))
                #list_N.append(1)
                ###

                shape = cv2.HuMoments(M).flatten()
                #print(type(cnt[0]))
                #print(cv2.HuMoments(M).flatten())
                #print(cnt.flatten())
                #print("-------------------------------------------------------------------------------------------------")
                #print(decimal.Decimal(shape[6]))
                #print(format((shape[0]), '20f'))
                #cv2.drawContours(frame, cnt, -1, (0,0,255), 3, 8)
                if area > areaTH: #and (peri > 950 and peri < 2500):

                    #####################
                    #   RASTREAMENTO    #
                    #####################

                    #Falta agregar condicoes para multiplas pessoas, saidas e entradas da tela

                    #M = cv2.moments(cnt)
                    #print("Antes dos filtros: ", M)
                    cx = int(M['m10']/M['m00'])
                    cy = int(M['m01']/M['m00'])

                    x, y, w, h = cv2.boundingRect(cnt)
                    dist = math.hypot(_center[0] - cx, _center[1] - cy)

                    # tentativa de remover retangulos muito largos
                    #if(x >= 240 or h >= 240):
                    #   continue

                    new = True
                    if cy in range(up_limit, down_limit):
                        #print("----------------------------------------------------------------")
                        #print(cnt)
                        #print("----------------------------------------------------------------")
                        #if(len(cnt) < 80):
                           # print("Possivel nao pessoa ................")
                            #continue
                        #print("Shape de nao pessoa: ", cv2.HuMoments(M).flatten())
                        for pessoa in pessoas:
                            if abs(cx - pessoa.getX()) <= w and abs(cy - pessoa.getY()) <= h:
                                # O objeto esta perto de um que ja foi detectado anteriormente
                                new = False
                                pessoa.updateCoords(cx,cy)   #atualizar coordenadas no objeto e reseta a idade
                                if pessoa.deslocaCima(line_down,line_up) == True: #  and shape[0] < 0.30:# and dist < 170 and dist > 70 : #and (pessoa.getOffset() - time.time() < -0.95):
                                    print("Diferenca de tempo: ", (pessoa.getOffset() - time.time()))
                                    cnt_up += 1;
                                    print ("ID: ",pessoa.getId(),'Entrou as',time.strftime("%c"))
                                    print("Area objeto: " + str(area))
                                    print("Distancia do centroide da pessoa: ", dist)
                                    print(M)
                                    print("Perimetro: ", peri)
                                    print("Shape da pessoa: ", shape[0] < 0.30)
                                    print("Shape da pessoa: ", shape[0] )
                                    list.append((cx,cy))
                                    list_P.pop()
                                    list_N.pop()
                                    list_P.append(np.float32(cv2.HuMoments(M)))
                                    #print(np.float32(cv2.HuMoments(M)))
                                    list_N.append(1)
                                    #trainingData = np.matrix(cnt, dtype=np.float32)
                                    #print("Training data ...... ")
                                    #print(trainingData)
                                elif pessoa.deslocaBaixo(line_down,line_up) == True : # and dist < 170 and dist > 70: # and (pessoa.getOffset() - time.time() < -0.95):
                                    print("Diferenca de tempo: ", (pessoa.getOffset() - time.time()))
                                    cnt_down += 1;
                                    print ("ID: ",pessoa.getId(),'Saiu as',time.strftime("%c"))
                                    print("Area objeto: " + str(area))
                                    print("Distancia do centroide da pessoa: ", dist)
                                    print(M)
                                    print("Perimetro: ", peri)
                                    print("Shape da pessoa: ", shape[0] < 0.30)
                                    print("Shape da pessoa: ", shape[0])
                                    list.append((cx, cy))
                                    list_P.pop()
                                    list_N.pop()
                                    list_P.append(np.float32(cv2.HuMoments(M)))
                                    #print(np.float32(cv2.HuMoments(M)))
                                    list_N.append(1)
                                    #trainingData = np.matrix(cnt, dtype=np.float32)
                                    #print("Training data ...... ")
                                    #print(trainingData)
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
                                del pessoa #libera a memoria de variavel i.
                        if new == True:
                            p = Pessoa.Pessoa(pid, cx, cy, max_p_age, time.time())
                            pessoas.append(p)
                            pid += 1
                    #################
                    #   DESENHOS    #
                    #################
                    cv2.circle(frame,(cx,cy), 5, (0,0,255), -1)
                    img = cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
                    #cv2.drawContours(frame, cnt, -1, (0,255,0), 3)

            #END for cnt in contours0

            #########################
            # DESENHAR TRAJETORIAS  #
            #########################
            for pessoa in pessoas:
                if len(pessoa.getTracks()) >= 2:
                   pts = np.array(pessoa.getTracks(), np.int32)
                   pts = pts.reshape((-1,1,2))
                   frame = cv2.polylines(frame,[pts],False,pessoa.getRGB())
                #if pessoa.getId() == 9:
                   #print (str(pessoa.getX()), ',', str(pessoa.getY()))
                cv2.putText(frame, str(pessoa.getId()),(pessoa.getX(),pessoa.getY()),font,0.3,pessoa.getRGB(),1,cv2.LINE_AA)

            #################
            #   IMAGEM      #
            #################
            str_up = 'Entraram '+ str(cnt_up)
            str_down = 'Sairam '+ str(cnt_down)
            tituloup = "Entrada "
            titulodown = "Saida "
            #dataehora = strftime("%c")
            dataehora = strftime("%A, %d %b %Y %H:%M:%S", gmtime())
            frame = cv2.polylines(frame,[pts_L1],False,line_down_color,thickness=1)
            frame = cv2.polylines(frame,[pts_L2],False,line_up_color,thickness=1)
            frame = cv2.polylines(frame,[pts_L3],False,(255,255,0),thickness=1)
            frame = cv2.polylines(frame,[pts_L4],False,(255,255,0),thickness=1)

            frame = cv2.polylines(frame,[pts_L5],False,(line_up_color),thickness=1)
            frame = cv2.polylines(frame,[pts_L6],False,(line_down_color),thickness=1)
            frame = cv2.polylines(frame,[pts_L7],False,(line_up_color),thickness=1)
            frame = cv2.polylines(frame,[pts_L8],False,(line_down_color),thickness=1)

            self.escreveCabecalho(frame, str_up, str_down, titulodown,tituloup,dataehora,font, x_meio)

            cv2.imshow('Frame',frame)
            cv2.imshow('Debug',mask)
            cv2.imshow('Binarizacao', imBin)

            #preisonar ESC para sair
            k = cv2.waitKey(30) & 0xff
            if k == 27:
                break
        #END while(cap.isOpened())

        #################
        #   LIMPEZA     #
        #################
        cap.release()
        cv2.destroyAllWindows()

    def escreveCabecalho(self,frame,str_up, str_down, titulodown, tituloup, dataehora, font, x_meio):
        cv2.putText(frame, str_up, (10, 40), font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, str_up, (10, 40), font, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(frame, str_down, (10, 60), font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, str_down, (10, 60), font, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, tituloup, (x_meio, 20), font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, titulodown, (x_meio, 450), font, 0.5, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, dataehora, (420, 20), font, 0.4, (255, 255, 255), 2, cv2.LINE_AA)

if __name__ == '__main__':
    c = Contador()
    c.detectPeople()