import qi
import sys
from naoqi import ALProxy
from inspect import getmodule
from multiprocessing import Pool

def async(decorated):
    r'''Wraps a top-level function around an asynchronous dispatcher.

        when the decorated function is called, a task is submitted to a
        process pool, and a future object is returned, providing access to an
        eventual return value.

        The future object has a blocking get() method to access the task
        result: it will return immediately if the job is already done, or block
        until it completes.

        This decorator won't work on methods, due to limitations in Python's
        pickling machinery (in principle methods could be made pickleable, but
        good luck on that).
    '''
    # Keeps the original function visible from the module global namespace,
    # under a name consistent to its __name__ attribute. This is necessary for
    # the multiprocessing pickling machinery to work properly.
    module = getmodule(decorated)
    decorated.__name__ += '_original'
    setattr(module, decorated.__name__, decorated)

    def send(*args, **opts):
        pool = Pool(processes=1)
        return pool.apply_async(decorated, args, opts)

    return send

class PostureController:

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.motion = ALProxy("ALMotion", ip, port)
        self.alife = ALProxy("ALAutonomousLife", ip, port)
        self.posture = ALProxy("ALRobotPosture", ip, port)
        self.navigation = ALProxy("ALNavigation", ip, port)

    def applyHomePosture(self):
        if(self.alife.getState() != "disabled"):
            self.alife.setState("disabled")
            #pass

        self.posture.goToPosture("StandInit", 1.0)

    def navigateTo(self, x, y):
        self.navigation.navigateTo(x,y)

    def explore(self, radius = 10):
        print("Starting looking for...")
        self.navigation.explore(radius)

    def onFinishedExploring(self):
        print("Didn't find")

    def stopExplore(self):
        print("Stopped looking for...")
        self.navigation.stopExploration()

    def rotate(self,degrees):
        from math import radians
        rad = radians(degrees)
        self.motion.moveTo(0,0,rad)
