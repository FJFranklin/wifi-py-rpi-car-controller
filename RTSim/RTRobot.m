classdef RTRobot < RTSim
    %RTRobot Controller for RTSim real-time robot simulation.
    %    https://github.com/FJFranklin/wifi-py-rpi-car-controller/tree/master/RTSim
    
    properties
        % list of global (class) variables used by setup(), loop() and ping_receive()
        target
        last_ping_time
        last_ping_distance
        position
        orientation
    end
    
    methods
        function obj = RTRobot (seconds, test_name)
            % This is the Matlab version of the coursework 'Matlab Robot':
            % In the following line, replace the number with your Student ID
            id_number = 170000000;

            if (nargin() < 1) % default to 180s (3 minutes)
                seconds = 180;
            end
            if (nargin() < 2) % default to simple layout
                test_name = 'default';
                % other options are: 'random', 'TNT', 'CWC' & 'BSB'
            end
            obj@RTSim (seconds, test_name, id_number);
        end
        function setup (obj) % setup() is called once at the beginning
            obj.target = obj.get_target ();       % where we are trying to get to

            % For example:
            obj.last_ping_time = 0;               % see ping_receive()
            obj.last_ping_distance = -1;
        end
        function loop (obj)
            % loop() is called repeatedly

            % For example:
            currentTime = obj.millis () / 1000;

            obj.position = obj.get_GPS ();        % roughly where we are
            obj.orientation = obj.get_compass (); % which direction we are looking

            if (currentTime > 4)
                obj.ping_send ();                 % it will not actually send more often than every 0.1s
            end

            obj.set_ping_angle (180);
            obj.set_wheel_speeds (-127, -126);
        end
        function ping_receive (obj, distance)
            % response to an obj.ping_send ()

            % For example:
            obj.last_ping_time = obj.millis ();   % the last time we received a ping [in milliseconds]
            obj.last_ping_distance = distance;    % distance measured (-ve if no echo)

            if (distance >= 0)                    % a -ve distance implies nothing seen
                disp (['position=(',num2str(obj.position(1)),',',num2str(obj.position(2)),...
                       '), orientation=',num2str(obj.orientation),...
                       '; distance=',num2str(distance)]);
            end
        end
    end
    
end

