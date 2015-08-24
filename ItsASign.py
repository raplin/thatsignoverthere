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
    print "\tNot running on a PI"
        
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
        for k,l in self.leds.iteritems():
            l.setActive(on)
        if not on:
            self.hardwareActive(on)

    def setLED(self,name,pwm):
        self.leds[name].setIntensity(pwm)
    
    def output(self):
        pass
    
    def getLEDs(self):
        return {}
    
    def fillNow(self,intensity=0):
        for k,l in self.leds.iteritems():
            l.setIntensity(intensity)
        self.update()

    def getLedKeys(self):
        return self.leds.keys()





class VideoSign(SignInterface):

    def __init__(self):
        SignInterface.__init__(self)
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

        self.size = (1000,900) #pygame.display.Info().current_w, pygame.display.Info().current_h)
        #self.size=(1280,1024) #(800,600)
        #self.window = pygame.display.set_mode(self.size, pygame.FULLSCREEN | pygame.HWSURFACE) #|pygame.DOUBLEBUF)
        self.window = pygame.display.set_mode(self.size, pygame.HWSURFACE) #|pygame.DOUBLEBUF)

        #self.window=pygame.display.set_mode((800,800))
        #self.surface = pygame.Surface(self.window.get_size())

        
    #pwm is 8 bit but intensity adjusted
    def setLED(self,name,intensity):
        self.leds[name].setIntensity(intensity)

    def output(self):
        self.render()
        pygame.display.flip()
        #pygame.display.update()

    def render(self):
        color=(0,0,0)   #erase last 
        self.window.fill(color,(0,0,self.size[0],self.size[1]))
        for k,l in self.leds.iteritems():
            l.output(self.window)
            


class LetteredVideoSign(VideoSign):

    class TextLetter(LightSegment):
        def __init__(self,name,char,font,x,y):
            LightSegment.__init__(self,name)
            self.char=char
            self.font=font
            self.pos=(x,y)

        def output(self,window):
            img=self.font.render( self.char , 1,(self.intensity,self.intensity,self.intensity))
            window.blit(img,self.pos)


    class ImageLetter(LightSegment):
        def __init__(self,name,image,x,y):
            LightSegment.__init__(self,name)
            self.image=image
            self.pos=(x,y)
    
        def output(self,window):
            if self.intensity>20:
                window.blit(self.image,self.pos)



class RaspberryPiLEDSign(SignInterface):
    
    class GPIODirectLetter(LightSegment):
        def __init__(self,name,pins,litLevel):
            LightSegment.__init__(self,name)
            self.pinList=pins
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
        def __init__(self,name,pins,tpicChip):
            LightSegment.__init__(self,name)
            self.tpicChip=tpicChip
            self.litLevel=0
            for p in pins:
                self.litLevel|= (1<<p)
                
        def output(self):
            if self.intensity>128:
                self.tpicChip.reg|= self.litLevel
            else:
                self.tpicChip.reg&= ~self.litLevel
        
    class TPICChip(object):
        TPIC_PWM_RATE=500

        def __init__(self,gpioClk,gpioData,gpioStrobe,gpioEnable):
            self.reg=0
            self.gpioClk=gpioClk
            self.gpioData=gpioData
            self.gpioStrobe=gpioStrobe
            self.gpioEnable=gpioEnable
            self.pwm=GPIO.PWM(gpioEnable,self.TPIC_PWM_RATE)
            self.pwmLevel=100

        def setActive(self,on):
            if on:
                self.pwm.stop()
            else:
                self.pwm.stop()

        def serialize(self):
            bit=1
            while bit<0x100:
                GPIO.output( self.gpioData, self.reg&bit )
                GPIO.output( self.gpioClk, 1)
                GPIO.output( self.gpioClk, 0)
                bit<<=1
        def strobe(self):
            GPIO.output( self.gpioStrobe, 1)
            GPIO.output( self.gpioStrobe, 0)
            self.pwm.start(self.pwmLevel)

    def __init__(self):
        SignInterface.__init__(self)
        self.leds=self.getLEDs()


    def hardwareActive(self,on):
        pass

    #pwm is 8 bit but intensity adjusted
    def setLED(self,name,pwm):
        self.leds[name].setIntensity(pwm)

    def output(self):
        for k,l in self.leds.iteritems():
            l.output()
        self.outputShifters()

    def outputShifters(self):
        pass #override

    
    

class ThatCampOverThereLEDSign(RaspberryPiLEDSign):

    def __init__(self):
        self.tpicChipA=self.TPICChip(9,10,11,0)
        self.tpicChipB=self.TPICChip(9,10,11,7)
        RaspberryPiLEDSign.__init__(self)
        #sets GPIO outputs for TPICs
        

    def getLEDs(self):
        letters=[
            #NEED fixing with real pin ids
            self.TPICShifterLetter( "T1", [0,1]    ,self.tpicChipB),
            self.GPIODirectLetter ( "H1", [1]      , 1 ),
            self.GPIODirectLetter ( "A1", [4]      , 1 ),
            self.TPICShifterLetter( "T2", [2,3]    ,self.tpicChipB),
            self.GPIODirectLetter ( "C1", [14]     , 1 ),
            self.GPIODirectLetter ( "A2", [23]     , 1 ),
            self.GPIODirectLetter ( "M1", [18]     , 1 ),
            self.TPICShifterLetter( "P1", [4,6,7]  ,self.tpicChipB),
            self.TPICShifterLetter( "o1", [0]      ,self.tpicChipA),
            self.TPICShifterLetter( "v1", [1]      ,self.tpicChipA ),
            self.TPICShifterLetter( "e1", [2]      ,self.tpicChipA ),
            self.TPICShifterLetter( "r1", [3]      ,self.tpicChipA ),
            self.TPICShifterLetter( "t1", [4]      ,self.tpicChipA ),
            self.TPICShifterLetter( "h1", [5]      ,self.tpicChipA ),
            self.TPICShifterLetter( "e2", [6]      ,self.tpicChipA ),
            self.TPICShifterLetter( "r2", [7]      ,self.tpicChipA ),
            self.TPICShifterLetter( "e3", [5]      ,self.tpicChipB ),
            self.GPIODirectLetter ( "01", [8]      , 1 ),
            self.GPIODirectLetter ( "11", [25]     , 1 ),
            self.GPIODirectLetter ( "21", [24]     , 1 ),
            self.GPIODirectLetter ( "31", [15]     , 1 ),
        ]
        lettermap={}
        for l in letters:
            lettermap[l.name]=l
        return lettermap;
        
    def outputShifters(self):
        self.tpicChipB.serialize()
        self.tpicChipA.serialize()
        self.tpicChipA.strobe()
        



class ThatCampOverThereVideoSign(LetteredVideoSign):
    #figure out rendered visuals to correspond to the LEDs
    def getLEDs(self):
        x=0
        y=0
        text=[ "THAT","CAMP","over there","0123" ]
        letteridx={}
        leds={}
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
                    letterKey="%s%d" % (char,cidx)
                    
                    if char.isdigit():
                        img=self.images["arrow"]
                        letter=self.ImageLetter( letterKey,img,cx,y)
                    else:
                        letter=self.TextLetter( letterKey,char,self.font,cx,y)
                    leds[letterKey]=letter
                cx+=self.fontW
            y+=self.fontH
            cx=x
        return leds


            



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
        self.interfaces.append( ThatCampOverThereLEDSign() )

        self.run()
        
    def quit(self):
        for i in self.interfaces:
            i.setActive(0)
        self.terminate=True
        time.sleep(0.5)
    
    """
    #prerender to blits is faster if required
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
            i.output()
            

    def runLogic(self):
        leds=self.interfaces[0].getLedKeys()
        now=int(time.time())
        val=0
        if now&2:
            val=255
        for l in leds:
            self.interfaces[0].setLED( l , val )
            self.interfaces[1].setLED( l , val )


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
