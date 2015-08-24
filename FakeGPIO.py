
class FakeGPIO(object):

    BCM=0
    OUT=0
    IN=0
    OUTPUT=0
    PUD_UP=0
    FALLING=0

    class pwMEH(object):
        def start(self,eh):
            pass
        def stop(self):
            pass
        def ChangeDutyCycle(self,meh):
            pass
    
    @classmethod
    def PWM(cls,meh,eh):
        return cls.pwMEH()

    @classmethod
    def setwarnings(cls,pm):
        pass

    @classmethod
    def setmode(cls,meh):
        pass


    @classmethod
    def output(cls,meh,eh):
        pass

    @classmethod
    def setup(cls,pin,meh,pull_up_down=False):
        pass

    @classmethod
    def add_event_detect(cls,pin,meh):
        pass

    @classmethod
    def event_detected(cls,meh):
        pass