# peopleCounter

https://contest.embarcados.com.br/projetos/iot-cam-ericsson/

**Intro: Cambus - System of Data Collection on Urban
Bus**

Among the
problems and difficulties known in public transport, the population lacks real
time information and with the least assertiveness. The overcrowding of public
transportation buses drives users away, who prefer to use their own vehicles,
even though they are still in traffic for hours. If real-time information, such
as the number of buses, is easily available to a user, he can choose whether to
wait for the next bus or to get around by bus or use a vehicle of his own. The
power of choice makes public transportation a more attractive option for the
user.

Counting
or estimating people indoors can be done in many ways, among which the most
commonly employed are:

- Thermal images

- Computer vision 

- Face counter

Among the
several difficulties to estimate people in an environment using computer
vision, the main ones are:

- Occlusions of people

- Inverting lighting

- Static occlusion, that is,
     people behind objects

- Camera angle to environment

A
challenge for this project is to know the correct angle of the camera that will
best aid in the subtraction of the background of the image, as well as the variable
luminosity during the day inside the bus.

The main
objective of the proposal is to create a robust and configurable model to
estimate overcrowding and make the results available to the population through
smartphones, etc.

### Step 1: Install Linaro in Dragonboard 410c

Follow the instructions to install Linaro 17.09 in DragonBoard 410c. We
recomend to install Linaro 17.09 to get kernel support for GPS.

 

### Step 2: Download Source Code From GitHub

Cambus has a modular architecture and code design. It's possible to code
your own machine learning algorithm, change to other cloud service and create
your own user applications.

To run the cambus project, first you need to download the source code from
github. Install python(Cambus was mode to run on verison 2.7 and &gt; 3.x) and
the following libraries using 'pip'(sudo apt-get install python-pip). It will
be needed to install a bunch of libraries in Linaro system(Also, It is
recomended to create a virtual enviroment - pip install virtualenv - in order
to isolate the Cambus system from the SO). Please, install the following
libraries:

```bash
pip install paho-mqtt

pip install numpy

pip install opencv-python

pip install twilio
```

Make sure if all libraries was installed and execute python CamBus_v1.py.
For while are using a video not a camera itself. Some changes will be needed in
the code regarding the fact we are using a video to simulate a camera on a bus.
For testing we have created a account on AWS, Dweet.io and Twilio. An Android
application was made to simulate a integration among all layers. 

Mind that some change has to be made to your condition about video size,
camera angle, luminosity etc. Every type of video has to be it's own parameters
adapation such as opencv kernel suctraction background and so on.
