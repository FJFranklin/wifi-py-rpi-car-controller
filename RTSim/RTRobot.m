classdef RTRobot < RTSim
    %RTRobot Controller for RTSim real-time robot simulation.
    %   Detailed explanation goes here
    
    properties
        % list of global variables used by both setup() and loop()
        target
    end
    
    methods
        function obj = RTRobot (seconds)
            obj@RTSim (seconds);
        end
        function setup (obj)
            % setup() is called once at the beginning

            % For example:
            obj.set_wheel_speeds (10, 25); % let's just go round in a circle
            
            % or, for a more challenging exercise, get a random target:
            % obj.target = obj.new_target ();
        end
        function loop (obj)
            % loop() is called repeatedly

            % For example:
            currentTime = (obj.millis () / 1000);

            % obj.set_ping_angle (currentTime * 20);
            obj.ping_send (); % it won't actually send more often than every 0.1s
        end
        function ping_receive (obj, distance)
            % response to an obj.ping_send ()
            if (distance >= 0) % a -ve distance implies nothing seen
                position = obj.get_GPS ();        % roughly where we are
                orientation = obj.get_compass (); % which direction we're looking
                disp (['position=(',num2str(position(1)),',',num2str(position(2)),...
                       '), orientation=',num2str(orientation),...
                       '; distance=',num2str(distance)]);
            end
        end
    end
    
end

