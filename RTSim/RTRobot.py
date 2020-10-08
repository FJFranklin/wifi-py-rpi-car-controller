from RTSim import RTSim

class RTRobot(RTSim):
    """
    RTRobot Controller for RTSim real-time robot simulation.
    https://github.com/FJFranklin/wifi-py-rpi-car-controller/tree/master/RTSim
    """

    def __init__(self, seconds=180, test_name='default'):
        # usage: RTRobot (seconds, test_name)
        # where test_name is one of 'default', 'random', 'TNT', 'CWC' or 'BSB'

        # This is the Python version of the coursework 'Matlab Robot':
        # In the following line, replace the number with your Student ID
        id_number = 170000000;

        RTSim.__init__(self, seconds, test_name, id_number)

    def setup(self):
        # setup() is called once at the beginning

        self.target = self.get_target()       # where we're trying to get to

        # For example:
        self.last_ping_time = 0               # see ping_receive()
        self.last_ping_distance = -1

        # To work out which of the trials we're running:
        results_so_far = self.get_result()
        test_name = results_so_far['Trial']
        print('This trial is:', test_name)

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
            print('position=(', self.position[0], ',', self.position[1], '), orientation=', self.orientation, '; distance=', distance, sep='')

if __name__ == "__main__":
    # Option to run from command line

    import argparse

    parser = argparse.ArgumentParser(description="RTRobot Coursework - Guide a two-wheeled robot round the map.")

    parser.add_argument('--duration', help='How many seconds to run [40].', default=40, type=int)
    parser.add_argument('--trial',    help='Specify map type [default].',   default='default', choices=['default', 'random', 'TNT', 'CWC', 'BSB'])

    args = parser.parse_args()

    R = RTRobot(args.duration, args.trial)
    print(R.get_result())
