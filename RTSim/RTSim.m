classdef RTSim < handle
    %RTSim Simulates a robot in a simple obstacle course.
    %   The robot starts in the top-left and must reach the bottom-right.
    %   RTSim should be subclassed, the subclass implementing Arduino-style
    %   loop() and setup() methods, as well as a ping_receive(distance)
    %   method:
    %   
    %     setup (obj)
    %     loop (obj)
    %     ping_receive (obj, range_to_target)
    %   
    %   The robot has two independently controlled wheels, and a
    %   sonar that can be rotated to any direction. The following controls
    %   are provided:
    %   
    %     RTSim(seconds) - The constructor sets up the simulation and runs
    %                      it for <seconds>, or until successful completion.
    %     get_target()   - Returns the current target to aim for.
    %     new_target()   - Sets (and returns) a random target to aim for.
    %     micros()       - Microseconds since program started.
    %     millis()       - Milliseconds since program started.
    %     set_wheel_speeds(left,right)
    %                    - Set left and right wheel speeds (-127..127).
    %     set_ping_angle(angle)
    %                    - Set angle (0..359) of sonar sensor.
    %     ping_send()    - Send a ping; the sonar takes 40ms to respond,
    %                      but 100ms before another ping can be sent.
    %     get_GPS()      - The current position; updates once a second.
    %     get_compass()  - The orientation [degrees]; updates once a second.
    
    properties (Access = private)
        timeStart    % simulation start time
        timeCurrent  % time in last/current motion-iteration
        position     % x [m], y [m], orientation [compass degrees]
                     % 2 rows: true / last measured
        speed        % left wheel [-127..127], right wheel [-127, 127]
                     % 3 rows: requested / set / actual
        pingTime     % time of last ping / time of response
        pingAngle    % sensor orientation, clockwise from forwards [degrees]
                     % 3 rows: requested / set / actual
        pingPoints   % record of ping responses for plotting
        pingCount    % number of ping responses
        posPoints    % record of robot positions for plotting
        posCount     % number of robot positions
        barriers     % list of rectangles making barriers
        target       % where to aim for to complete the course
        sim_fig      % the plotting window
    end
    methods (Abstract)
        setup (obj)
        loop (obj)
        ping_receive (obj, range_to_target)
    end
    methods
        function obj = RTSim (seconds)
            obj.barriers = [
                -5.05, -5.00,  0.05, 10;
                -5.00,  5.00, 10,     0.05;
                -5.00, -5.05, 10,     0.05;
                 5.00, -5.00,  0.05, 10;
                -3.00, -3.00,  0.05,  8;
                 2.95, -5.00,  0.05,  8;
                -1.00, -0.10,  2.00,  0.2
                ];
            obj.sim_fig = figure(1);

            obj.timeStart = cputime;
            obj.timeCurrent = 0;

            obj.position = zeros (2, 3);
            obj.speed = zeros (3, 2);
            obj.pingTime = -100 * ones (1, 2);
            obj.pingAngle = zeros (1, 3);
            obj.pingPoints = zeros (100, 2);
            obj.pingCount = 0;
            obj.posPoints = zeros (100, 2);
            obj.posCount = 0;

            obj.target = [4.5, -4.5];

            lastMicros = 0;
            lastMillis = 0;
            lastSecond = 0;
            count_ms = 0;
            count_20 = 0;

            % Start in the top-left
            obj.position(1,1:2) = [-4.5,4.5];
            obj.position(2,1:2) = obj.position(1,1:2);

            obj.update_figure ();

            obj.setup ();

            % Finish in the bottom-right
            while (norm (obj.position(1,1:2) - obj.target) > 0.5)
                thisTime = cputime - obj.timeStart;
                if (thisTime > seconds)
                    break;
                end

                if (obj.pingTime(1) > obj.pingTime(2))
                    if (thisTime - obj.pingTime(1) > 0.04) % 40ms after send
                        % disp(['pong, pingTime=',num2str(obj.pingTime(1)),', time=',num2str(thisTime)]);
                        obj.pingTime(2) = thisTime;
                        obj.ping_calculate ();
                    end
                end

                thisMicros = obj.micros ();
                if (lastMicros < thisMicros)
                    lastMicros = thisMicros;
                    obj.update_motion ();
                end

                thisMillis = obj.millis ();
                if (lastMillis < thisMillis)
                    count_ms = count_ms + (thisMillis - lastMillis);
                    lastMillis = thisMillis;
                    obj.update_servos (false); % servo-actual updates only

                    if (count_ms >= 20)
                        while (count_ms >= 20)
                            count_20 = count_20 + 1;
                            count_ms = count_ms - 20;
                        end

                        obj.update_servos (true); % servo-target updates only every 20ms

                        if (count_20 >= 25)
                            count_20 = count_20 - 25;
                            obj.update_figure (); % update figure every 0.5s
                        end
                    end
                end
                
                if (lastSecond < floor (thisTime)) % update measured position
                    lastSecond = floor (thisTime);
                    obj.update_position ();

                    obj.posCount = obj.posCount + 1;
                    obj.posPoints(obj.posCount,:) = obj.position(1,1:2);
                end

                obj.loop ();
            end
            if (norm (obj.position(1,1:2) - obj.target) <= 0.5)
                disp(['Success! Course completed in ',num2str(obj.millis()/1000),'s'])
            end
        end
        function pos = get_target (obj)
            pos = obj.target;
        end
        function pos = new_target (obj)
            obj.target = obj.position(1,1:2);
            while (norm (obj.position(1,1:2) - obj.target) < 3)
                obj.target = -4.5 + 9 * rand(1,2);
            end
            pos = obj.target;
        end
        function reset_barriers(obj, seed)
            rng (seed);
            par = rand(1,7);
            b1x = -3.5 + par(1);
            b1y1 = -4 + 2 * par(2);
            b1y2 = b1y1 + 1;
            b2x = 2.5 + par(3);
            b2y2 = 4 - 2 * par(4);
            b2y1 = b2y2 - 1;
            b3x1 = b1x + 1 + par(5);
            b3x2 = b2x - 1 - par(6);
            b3y = -1 + 2 * par(7);
            obj.barriers = [
                -5.05, -5.00,  0.05, 10;
                -5.00,  5.00, 10,     0.05;
                -5.00, -5.05, 10,     0.05;
                 5.00, -5.00,  0.05, 10;
                 b1x,   b1y2,  0.05,  5-b1y2;
                 b1x,  -5.00,  0.05,  b1y1-(-5.00);
                 b2x,   b2y2,  0.05,  5-b2y2;
                 b2x,  -5.00,  0.05,  b2y1-(-5.00);
                 b3x2-0.05,  b3y-2, 0.05,  2;
                 b3x1,  b3y+0.05, 0.05,  2;
                 b3x1,  b3y,   (b3x2-b3x1),  0.2
                ];
            rng (cputime);
            par = rand (1, 3);
            obj.position(1,3) = 359 * par(3);
            obj.position(1,2) = -4.5 + 9 * par(1);
            obj.target(1,2)   = -4.5 + 9 * par(2);
        end
        function t_us = micros (obj)
            t_us = floor (1000000 * (cputime - obj.timeStart));
        end
        function t_ms = millis (obj)
            t_ms = floor (1000 * (cputime - obj.timeStart));
        end
        function set_wheel_speeds (obj, left, right)
            if (left < -127)
                left = -127;
            elseif (left > 127)
                left = 127;
            else
                left = round (left);
            end
            if (right < -127)
                right = -127;
            elseif (right > 127)
                right = 127;
            else
                right = round (right);
            end
            obj.speed(1,:) = [left, right];
        end
        function set_ping_angle (obj, angle)
            while (angle >= 360)
                angle = angle - 360;
            end
            while (angle < 0)
                angle = angle + 360;
            end
            obj.pingAngle(1) = round (angle);
        end
        function ping_send (obj)
            thisTime = cputime - obj.timeStart;
            if (thisTime - obj.pingTime >= 0.1) % 100 milliseconds
                obj.pingTime(1) = thisTime;
                % disp (['ping, time=',num2str(thisTime)]);
            end
        end
        function position = get_GPS (obj)
            position = obj.position(2,1:2);
        end
        function orientation = get_compass (obj)
            orientation = obj.position(2,3);
        end
    end
    methods (Access=private)
        function update_motion (obj)
            thisTime = cputime - obj.timeStart;
            dt = thisTime - obj.timeCurrent;
            obj.timeCurrent = thisTime;

            speed_l = obj.speed(3,1) / 508; % -0.25..0.25m/s
            speed_r = obj.speed(3,2) / 508; % -0.25..0.25m/s
            pos = obj.position(1,1:2);
            ori = obj.position(1,3); % compass degrees

            if (speed_l == speed_r)
                dir = [sind(ori), cosd(ori)];
                pos = pos + dir * speed_l * dt;
            elseif (speed_l + speed_r == 0)
                ang_speed = speed_l / 0.1; % clockwise
                theta = ang_speed * dt; % radians
                % So new position & orientation:
                ori = ori + theta * 180 / pi;
            else
                % Vector to wheel from robot centre
                wheel = 0.1 * [cosd(ori), -sind(ori)];
                % Centre of motion
                gamma = (speed_l + speed_r) / (speed_l - speed_r);
                centre = pos + gamma * wheel;
                % Radius of motion
                radius = gamma / 10;
                % Tangential & angular speed of robot centred at pos
                av_speed = (speed_l + speed_r) / 2;
                ang_speed = av_speed / radius; % radians/s - clockwise
                % Movement, therefore:
                theta = ang_speed * dt; % radians
                % So new position & orientation:
                ori = ori + theta * 180 / pi;
                vec = pos - centre;
                cos_theta = cos (theta);
                sin_theta = sin (theta);
                vec = [vec(1)*cos_theta+vec(2)*sin_theta,...
                      -vec(1)*sin_theta+vec(2)*cos_theta];
                pos = centre + vec;
            end
            if (obj.position_valid (pos))
                obj.position(1,1:2) = pos;
                while (ori >= 360)
                    ori = ori - 360;
                end
                while (ori < 0)
                    ori = ori + 360;
                end
                obj.position(1,3) = ori;
            else
            	obj.speed(3,1) = 0;
            	obj.speed(3,2) = 0;
            end
        end
        function update_servos (obj, bTargetUpdate)
            if (bTargetUpdate)
                obj.speed(2,:) = obj.speed(1,:);
                obj.pingAngle(2) = obj.pingAngle(1);
            else
                if (obj.speed(3,1) > obj.speed(2,1))
                    obj.speed(3,1) = obj.speed(3,1) - 1;
                end
                if (obj.speed(3,1) < obj.speed(2,1))
                    obj.speed(3,1) = obj.speed(3,1) + 1;
                end
                if (obj.speed(3,2) > obj.speed(2,2))
                    obj.speed(3,2) = obj.speed(3,2) - 1;
                end
                if (obj.speed(3,2) < obj.speed(2,2))
                    obj.speed(3,2) = obj.speed(3,2) + 1;
                end
                pingDiff = obj.pingAngle(3) - obj.pingAngle(2);
                if (pingDiff)
                    if (((pingDiff >= 0) && (pingDiff <= 180)) || (pingDiff <= -180))
                        obj.pingAngle(3) = obj.pingAngle(3) - 1;
                        if (obj.pingAngle(3) < 0)
                            obj.pingAngle(3) = 359;
                        end
                    else
                        obj.pingAngle(3) = obj.pingAngle(3) + 1;
                        if (obj.pingAngle(3) > 359)
                            obj.pingAngle(3) = 0;
                        end
                    end
                end
            end
        end
        function update_figure (obj)
            figure (obj.sim_fig);
            clf;
            %axis([-5.1,-1.9,1.9,5.1]);
            axis([-5.1,5.1,-5.1,5.1]);

            % the barriers
            count = size (obj.barriers, 1);
            for c = 1:count
                rectangle('Position',obj.barriers(c,:),'FaceColor',[0 .5 .5])
            end
            % the target
            target = [obj.target(1,1:2)-0.3,0.6,0.6];
            rectangle('Position',target,'Curvature',[1 1],'EdgeColor',[1 0.5 0.5])
            % the robot
            bot = [obj.position(1,1:2)-0.2,0.4,0.4];
            rectangle('Position',bot,'Curvature',[1 1],'FaceColor',[1 0.5 0.5])
            wheel = [0.09,-0.1;0.09,0.1;0.13,0.1;0.13,-0.1;0.09,-0.1];
            angle = obj.position(1,3); % clockwise from North in degrees
            obj.draw_poly (obj.position(1,1:2),  wheel, angle, 'blue', 'none');
            obj.draw_poly (obj.position(1,1:2), -wheel, angle, 'blue', 'none');
            arrow = [0,0.2;0.09,0;-0.09,0;0,0.2];
            obj.draw_poly (obj.position(1,1:2), arrow, angle, 'black', 'none');
            % the sonar beam
            % disp(['angle=',num2str(angle),', pingAngle=',num2str(obj.pingAngle(3))]);
            angle = angle + obj.pingAngle(3);
            sonar = [0,0;-0.05,1;0.05,1;0,0];
            obj.draw_poly (obj.position(1,1:2), sonar, angle, 'red', 'none');
            % 
            hold on;
            if (obj.pingCount)
                plot (obj.pingPoints(1:obj.pingCount,1),obj.pingPoints(1:obj.pingCount,2),'r*');
            end
            if (obj.posCount)
                plot (obj.posPoints(1:obj.posCount,1),obj.posPoints(1:obj.posCount,2),'k^');
            end
            text(3.0,4.7,['Time: ',num2str(obj.millis()/1000),'s']);
            hold off;
            drawnow
        end
        function draw_poly (~, offset, vertices, angle, face_color, edge_color)
            cos_a =  cosd (angle);
            sin_a = -sind (angle);
            X = vertices(:,1)*cos_a-vertices(:,2)*sin_a;
            Y = vertices(:,1)*sin_a+vertices(:,2)*cos_a;
            patch(offset(1)+X,offset(2)+Y,face_color,'EdgeColor',edge_color);
        end
        function update_position (obj) % update measured position
            obj.position(2,1:2) = round (obj.position(1,1:2), 2);
            obj.position(2,3) = round (obj.position(1,3));
            if (obj.position(2,3) == 360)
                obj.position(2,3) = 0;
            end
        end
        function ping_calculate (obj)
            angle = 90 - (obj.position(1,3) + obj.pingAngle(3));
            while (angle < 0)
                angle = angle + 360;
            end
            dir = [cosd(angle), sind(angle)];
            pos = obj.position (1,1:2);
 
            count = size (obj.barriers, 1);
            closest_distance = -1;
            closest_point = [0,0];
            for c = 1:count
                line = [obj.barriers(c,1),obj.barriers(c,2),...
                        obj.barriers(c,1)+obj.barriers(c,3),obj.barriers(c,2)];
                [distance,point] = obj.intersection (pos, dir, line);
                if ((distance >= 0) && ((closest_distance < 0) || (distance < closest_distance))) % we have an intersection
                    closest_distance = distance;
                    closest_point = point;
                end
                line = [obj.barriers(c,1),obj.barriers(c,2),...
                        obj.barriers(c,1),obj.barriers(c,2)+obj.barriers(c,4)];
                [distance,point] = obj.intersection (pos, dir, line);
                if ((distance >= 0) && ((closest_distance < 0) || (distance < closest_distance))) % we have an intersection
                    closest_distance = distance;
                    closest_point = point;
                end
                line = [obj.barriers(c,1)+obj.barriers(c,3),obj.barriers(c,2)+obj.barriers(c,4),...
                        obj.barriers(c,1),obj.barriers(c,2)+obj.barriers(c,4)];
                [distance,point] = obj.intersection (pos, dir, line);
                if ((distance >= 0) && ((closest_distance < 0) || (distance < closest_distance))) % we have an intersection
                    closest_distance = distance;
                    closest_point = point;
                end
                line = [obj.barriers(c,1)+obj.barriers(c,3),obj.barriers(c,2)+obj.barriers(c,4),...
                        obj.barriers(c,1)+obj.barriers(c,3),obj.barriers(c,2)];
                [distance,point] = obj.intersection (pos, dir, line);
                if ((distance >= 0) && ((closest_distance < 0) || (distance < closest_distance))) % we have an intersection
                    closest_distance = distance;
                    closest_point = point;
                end
            end
            % disp (['closest distance=',num2str(closest_distance)]);
            % disp (closest_point);
            if (closest_distance >= 0)
                obj.pingCount = obj.pingCount + 1;
                obj.pingPoints(obj.pingCount,:) = closest_point;
                obj.ping_receive (round (closest_distance, 2));
            end
        end
        function [distance,point] = intersection(~, pos, dir, line)
            distance = -1; % no intersection
            point = pos;

            % lines are horizontal or vertical
            if ((line(1) == line(3)) && dir(1)) % vertical
                t = (line(1) - pos(1)) / dir(1);
                if ((t >= 0) && (t <= 1))
                    s = (t * dir(2) - (line(2) - pos(2))) / (line(4) - line(2));
                    if ((s >= 0) && (s <= 1)) % valid intersection
                        point = t * dir + pos;
                        distance = t;
                    end
                end
            end
            if ((line(2) == line(4)) && dir(2)) % horizontal
                t = (line(2) - pos(2)) / dir(2);
                if ((t >= 0) && (t <= 1))
                    s = (t * dir(1) - (line(1) - pos(1))) / (line(3) - line(1));
                    if ((s >= 0) && (s <= 1)) % valid intersection
                        point = t * dir + pos;
                        distance = t;
                    end
                end
            end
        end
        function bValidity = position_valid (obj, pos)
            bValidity = true;

            count = size (obj.barriers, 1);
            for c = 1:count
                % discard barriers that are obviously too far away
                if (obj.barriers(c,1) - pos(1) > 0.2)
                    continue;
                end
                if (pos(1) - (obj.barriers(c,1) + obj.barriers(c,3)) > 0.2)
                    continue;
                end
                if (obj.barriers(c,2) - pos(2) > 0.2)
                    continue;
                end
                if (pos(2) - (obj.barriers(c,2) + obj.barriers(c,4)) > 0.2)
                    continue;
                end
                % Check corners first
                if (((obj.barriers(c,1) - pos(1))^2 + ...
                     (obj.barriers(c,2) - pos(2))^2)^0.5 < 0.2)
                     bValidity = false;
                     break;
                end
                if (((obj.barriers(c,1) + obj.barriers(c,3) - pos(1))^2 + ...
                     (obj.barriers(c,2) - pos(2))^2)^0.5 < 0.2)
                     bValidity = false;
                     break;
                end
                if (((obj.barriers(c,1) - pos(1))^2 + ...
                     (obj.barriers(c,2) + obj.barriers(c,4) - pos(2))^2)^0.5 < 0.2)
                     bValidity = false;
                     break;
                end
                if (((obj.barriers(c,1) + obj.barriers(c,3) - pos(1))^2 + ...
                     (obj.barriers(c,2) + obj.barriers(c,4) - pos(2))^2)^0.5 < 0.2)
                     bValidity = false;
                     break;
                end
                % Finally check barrier lines
                line = [obj.barriers(c,1),obj.barriers(c,2),...
                        obj.barriers(c,1)+obj.barriers(c,3),obj.barriers(c,2)];
                if (obj.barriers(c,2) >= pos(2))
                    dir = [0,1];
                else
                    dir = [0,-1];
                end
                [distance,~] = obj.intersection (pos, dir, line);
                if ((distance >= 0) && (distance < 0.2)) % we have an intersection
                    bValidity = false;
                    break;
                end
                line = [obj.barriers(c,1),obj.barriers(c,2),...
                        obj.barriers(c,1),obj.barriers(c,2)+obj.barriers(c,4)];
                if (obj.barriers(c,1) >= pos(1))
                    dir = [1,0];
                else
                    dir = [-1,0];
                end
                [distance,~] = obj.intersection (pos, dir, line);
                if ((distance >= 0) && (distance < 0.2)) % we have an intersection
                    bValidity = false;
                    break;
                end
                line = [obj.barriers(c,1)+obj.barriers(c,3),obj.barriers(c,2)+obj.barriers(c,4),...
                        obj.barriers(c,1),obj.barriers(c,2)+obj.barriers(c,4)];
                if (obj.barriers(c,2) + obj.barriers(c,4) >= pos(2))
                    dir = [0,1];
                else
                    dir = [0,-1];
                end
                [distance,~] = obj.intersection (pos, dir, line);
                if ((distance >= 0) && (distance < 0.2)) % we have an intersection
                    bValidity = false;
                    break;
                end
                line = [obj.barriers(c,1)+obj.barriers(c,3),obj.barriers(c,2)+obj.barriers(c,4),...
                        obj.barriers(c,1)+obj.barriers(c,3),obj.barriers(c,2)];
                if (obj.barriers(c,1) + obj.barriers(c,3) >= pos(1))
                    dir = [1,0];
                else
                    dir = [-1,0];
                end
                [distance,~] = obj.intersection (pos, dir, line);
                if ((distance >= 0) && (distance < 0.2)) % we have an intersection
                    bValidity = false;
                    break;
                end
            end
        end
    end
    
end

