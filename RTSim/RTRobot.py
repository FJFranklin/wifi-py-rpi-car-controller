from RTSim import RTSim

class RTRobot(RTSim):
    """
    RTRobot Controller for RTSim real-time robot simulation.
    https://github.com/FJFranklin/wifi-py-rpi-car-controller/tree/master/RTSim
    """

    def __init__(self, seconds):
        # usage: RTRobot (seconds)
        RTSim.__init__(self, seconds)

    def setup(self):
        # setup() is called once at the beginning

        # This is the Python version of the MEC3014 Courswork 'Matlab Robot':
        # Replace the number in the following line with your Student ID
        self.reset_barriers(160000000)
        self.target = self.get_target()       # where we're trying to get to

        # For example:
        self.last_ping_time = 0               # see ping_receive()
        self.last_ping_distance = -1

    def loop(self):
        # loop() is called repeatedly

        # For example:
        currentTime = self.millis() / 1000

        self.position = self.get_GPS()        # roughly where we are
        self.orientation = self.get_compass() # which direction we're looking

        if currentTime > 4:
            self.ping_send()                  # it won't actually send more often than every 0.1s

        self.set_ping_angle(180)
        self.set_wheel_speeds(-127, -126)

    def ping_receive(self, distance):
        # response to an self.ping_send()

        # For example:
        self.last_ping_time = self.millis()  # the last time we received a ping [in milliseconds]
        self.last_ping_distance = distance   # distance measured (-ve if no echo)

        if distance >= 0:                    # a -ve distance implies nothing seen
            print('position=(', self.position[0], ',', self.position[1], '),orientation=', self.orientation, '; distance=', distance, sep='')
