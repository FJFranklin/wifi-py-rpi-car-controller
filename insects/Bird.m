classdef Bird < Camera
    %Bird A bird to fly in the insect field
    
    properties
        speed
        eaten
    end
    
    methods
        function obj = Bird(environment, sight_range)
            %Bird A bird to fly in the insect field
            obj@Camera(environment, sight_range);

            obj.speed = 10;
            obj.eaten = 0;
            obj.adjust_limit = 30; % allow tilt/heading to adjust by up to 30 deg/s
        end
        
        function targets = update(obj, dt, delta_heading, delta_tilt, target_speed)
            %update Update bird position and orientation; look for insects.

            % update heading & tilt
            obj.adjust(dt, delta_heading, delta_tilt);
            if obj.tilt > 135
                obj.tilt = 135;
            elseif obj.tilt < 45
                obj.tilt = 45;
            end
            
            % update speed (1-20 m/s); limiting acceleration is 1 m/s2
            limit = 1 * dt;
            dv = target_speed - obj.speed;
            if dv > 0
                if dv > limit
                    dv = limit;
                end
                obj.speed = obj.speed + dv;
                if obj.speed > 20
                    obj.speed = 20;
                end
            elseif dv < 0
                if (-dv) > limit
                    dv = -limit;
                end
                obj.speed = obj.speed + dv;
                if obj.speed < 1
                    obj.speed = 1;
                end
            end

            dr = obj.speed * dt;
            dz = dr * sind(obj.tilt - 90);
            dr = dr * cosd(obj.tilt - 90);
            dx = dr * cosd(90 - obj.heading);
            dy = dr * sind(90 - obj.heading);
            
            % update bird position
            obj.position(1) = obj.E.wrap(obj.position(1) + dx, obj.E.side);
            obj.position(2) = obj.E.wrap(obj.position(2) + dy, obj.E.side);
            obj.position(3) = obj.E.wrap(obj.position(3) + dz, obj.E.side);

            targets = obj.snap();
            if min(targets(:,3)) < 0.1
                obj.eaten = obj.eaten + 1;
            end
            text(-1.5, 1.0, 'Speed:')
            text(-1.5, 0.8, 'Eaten:')
            text(-1.0, 1.0, num2str(obj.speed))
            text(-1.0, 0.8, num2str(obj.eaten))
        end
    end
    
    methods(Static)
        function demo()
            E = Environment(60, 500, false);
            B = Bird(E, 20);

            dt = 0.1; % time-step [s]
            while ishandle(B.fig)
                E.update(dt);

                delta_heading = 1; % change in heading: compass direction 0-359 degrees
                delta_tilt    = 0; % change in tilt:    0 = down; 90 = level; 180 = up
                target_speed  = 5; % 1 (slowest); 20 (fastest)
                targets = B.update(dt, delta_heading, delta_tilt, target_speed);
                % targets is a matrix where each row represents an insect and the
                % three columns are X, Y, R, where R is the distance to the insect

                pause(dt)
            end
        end
    end
end

