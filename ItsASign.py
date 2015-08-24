import pygame
import time,os,threading
from pygame.locals import *
import random
import glob

try:
    import RPi.GPIO as GPIO
    import smbus
    Pi=True
    
except:
    from FakeGPIO import FakeGPIO as GPIO
    Pi=False

NUM_CHANNELS=18

class LightSegment(object):
    def __init__(self,name):
        self.intensity=0
        self.name=name

    def setActive(self,on):
        pass

    def setIntensity(self,intensity):
        self.intensity=intensity

    def output(self):
        pass



class SignInterface(object):
    def setActive(self,on):
        if on:
            self.hardwareActive(on)
        for l in self.leds:
            l.setActive(on)
        if not on:
            self.hardwareActive(on)

    def setLED(self,name,pwm):
        pass
    def flip(self):
        pass
    def getLEDs(self):
        return {}





class VideoSign(SignInterface):

    def __init__(self):
        self.images={}
        for fileName in glob.glob("images/*"):
            imageId=fileName.replace("\\","/").split("/")[-1].split(".")[0]
            self.images[imageId] = pygame.image.load(fileName)
        self.fontW=96 #64
        self.fontH=170 #95
        self.font=pygame.font.SysFont("Arial",120, bold=True, italic=False)

        self.leds=self.getLEDs()
        

    def hardwareActive(self,on):
        if not on:
            pygame.display.quit()
            return

        pygame.display.init()

        self.size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        #self.size=(1280,1024) #(800,600)
        #self.window = pygame.display.set_mode(self.size, pygame.FULLSCREEN | pygame.HWSURFACE) #|pygame.DOUBLEBUF)
        self.window = pygame.display.set_mode(self.size, pygame.HWSURFACE) #|pygame.DOUBLEBUF)

        #self.window=pygame.display.set_mode((800,800))
        #self.surface = pygame.Surface(self.window.get_size())

        
    #pwm is 8 bit but intensity adjusted
    def setLED(self,index,pwm):
        pass

    def flip(self):
        self.render()
        pygame.display.flip()
        #pygame.display.update()

    def render(self):
        color=(0,0,0)   #erase last 
        self.window.fill(color,(0,0,self.size[0],self.size[1]))
        for led in self.leds:
            led.output()
            


class LetteredVideoSign(VideoSign):

    class TextLetter(LightSegment):
        def __init__(self,name,char,font,x,y):
            LightSegment.__init__(self,name)
            self.char=char
            self.font=font
            self.pos=(x,y)

        def output(self):
            img=self.font.render( char , 1,(self.intensity,self.intensity,self.intensity))
            window.blit(img,self.pos)


    class ImageLetter(LightSegment):
        def __init__(self,name,image,x,y):
            LightSegment.__init__(self,name)
            self.image=image
            self.pos=(x,y)
    
        def output(self):
            if self.intensity>20:
                window.blit(self.image,self.pos)



class RaspberryPiLEDSign(SignInterface):
    
    class GPIODirectLetter(LightSegment):
        def __init__(self,name,bits,litLevel):
            LightSegment.__init__(self,name)
            self.bits=bits
            self.pinList=[]
            for n in range(32):
                if bits & (1<<n):
                    self.pinList.append(n)
            self.litLevel=litLevel  #1=on or 0=on 

        def setActive(self,on):
            for pin in self.pinList:
                if on:
                    GPIO.setup(pin,GPIO.OUTPUT)
                GPIO.output(pin,1-self.litLevel)

        def output(self):
            for pin in self.pinList:
                if self.intensity>128:
                    GPIO.output(pin,self.litLevel)
                else:
                    GPIO.output(pin,1-self.litLevel)


    class TPICShifterLetter(LightSegment):
        def __init__(self,name,pin,tpicChip):
            LightSegment.__init__(self,name)
            self.pin=pin
            self.tpicChip=tpicChip
            self.litLevel=1<<pin
            
        def output(self):
            if self.intensity>128:
                self.tpicChip.reg|= self.litLevel
            else:
                self.tpicChip.reg&= ~self.litLevel
        
    class TPICChip(object):
        def __init__(self):
            self.reg=0


    
        
    #pwm is 8 bit but intensity adjusted
    def setLED(self,index,pwm):
        pass

    def flip(self):
        #pygame.display.update()

    def off(self):
        pygame.display.quit()

    

class ThatCampOverThereLEDSign(LEDSign):

    def __init__(self):
        LEDSign.__init__(self)

        self.tpicChipA=self.TPICChip()
        self.tpicChipB=self.TPICChip()
        

    def getLEDs(self):
        lettermap={
            "T": self.TPICShifterLetter( "T1", (1<<0)|(1<<1) ),
            "H": self.GPIODirectLetter ( "H1", (1 , 1 ),
            "A": self.GPIODirectLetter ( "H1", 1 , 1 ),
        }

        return 
            


class ThatCampOverThereVideoSign(LetteredVideoSign):
    #figure out rendered visuals to correspond to the LEDs
    def getLEDs(self):
        x=0
        y=0
        text=[ "THAT","CAMP","over there","0123" ]
        letteridx={}
        map={}
        cx=x    
        for line in text:
            for char in line:
                if char!=" ":
                    cidx=1
                    if char in letteridx:
                        cidx=letteridx[char]
                    else:
                        cidx=0
                    cidx+=1
                    letteridx[char]=cidx
                    letterKey="%s%d" % (char,letteridx)
                    
                    if char.isdigit():
                        img=self.images["arrow"]
                        letter=self.ImageLetter( letterKey,img,cx,y)
                    else:
                        letter=self.TextLetter( letterKey,char,self.font,cx,y)
                    letteridx[letterKey]=letter
                cx+=self.fontW
            y+=self.fontH
            cx=x
        print letteridx
        return letteridx


            
class RaspberryPiDriver(SignInterface):
    def __init__(self):
        pass


class ThatCampOverThereLEDSign(LEDSign):

    
    def getLEDs(self):
        text=[ "THAT","CAMP","over there","0123" ]
        
        return 
            



class CampSign(object):
    def start(self):
        pygame.init()
    
        pygame.mixer.init()
        self.samples={}
        for fileName in glob.glob("samples/edits/*.wav"):
            sampleId=fileName.replace("\\","/").split("/")[-1].split(".")[0]
            self.samples[sampleId]=pygame.mixer.Sound(fileName)
        
        print self.samples.keys()
        
        self.interfaces=[]
        self.interfaces.append( ThatCampOverThereVideoSign() )
        self.interfaces.append( LEDSign() )

        self.run()
        
    def quit(self):
        for i in self.interfaces:
            i.setActive(0)
        self.terminate=True
        time.sleep(0.5)
    
    """
    def renderDigits(self):
        self.digits={}
        for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ|<>":
            d= pygame.Surface((self.fontW,self.fontH))
            text=self.font.render( c , 1,(255,255,255))
            d.blit(text,(0,0))
            self.digits[c]=d
    """
    
    def run(self):
        self.FPS=20
        self.terminate=False
        self.fpsClock=pygame.time.Clock()

        for i in self.interfaces:
            i.setActive(1)


        #self.renderDigits()
        
        self.frameCounter=0
        
        self.arcChannel=0

        
        #run with faked vsync?
        stop=False
        self.popCount=0
        while not self.terminate and not stop:
            self.frameCounter+=1

            self.runLogic()
            
            self.updateDisplay()

            self.fpsClock.tick(self.FPS)

            for event in pygame.event.get():
                if event==QUIT or event.type==KEYDOWN:
                    stop=True

        #pygame.event.post(pygame.event.Event(QUIT))
        pygame.quit()

    def updateDisplay(self):
        for i in self.interfaces:
            i.flip()
        
        

    def runLogic(self):
        for 
        pass
        """
        x=0
        y=0
        
        worksFineSequence=[ 1,3, ]

        text=[ "THAT\n","CAMP\n","OVER ","THERE","!" ]
        color=(0,0,0)   #erase last 
        self.window.fill(color,(0,0,self.size[0],self.size[1]))

        worksFine=int(time.time()) & 8

        if self.popCount:
            self.popCount-=1
            return
        if not worksFine:
            doPop=random.randrange(0,128)
            if doPop>125:
                self.popCount=100
                self.arcChannel.stop()
                self.popChannel = self.samples["pop!"].play()
                return
            if not self.arcChannel or not self.arcChannel.get_busy():
                self.arcChannel = self.samples["arc3"].play()

        else:
            if self.arcChannel:
                self.arcChannel.stop()


        cx=x    
        for line in text:
            wordSuppress=False
            wordFlicker=random.randrange(0,64)
            if wordFlicker<1:
                wordSuppress=True
            charSuppress=0
            if wordFlicker<2:
                charSuppress=random.randrange(0,5)
            for char in line:
                if char=="\n":
                    continue
                intensity=255
                onOff=random.randrange(0,24)
                
                if onOff<4 and not worksFine:
                    intensity=random.randrange(200,255)
                if wordSuppress or charSuppress or onOff==0:
                    intensity=0
                if char!=" " and intensity:
                    img=None
                    if char=="!":
                        if intensity>128:
                            img=self.images["arrow"]
                    else:
                        img=self.font.render( char , 1,(intensity,intensity,intensity))
                    if img:
                        self.window.blit(img,(cx,y))
                if charSuppress:
                    charSuppress-=1
                cx+=self.fontW
            if line[-1]=="\n":
                y+=self.fontH
                cx=x
        """    
        
       

if True:
    h=CampSign()
    h.start()
