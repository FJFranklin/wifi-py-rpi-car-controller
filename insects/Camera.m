classdef Camera < handle
    %Camera A distorted perspective view of the insect field
    
    properties
        E
        sight
        adjust_limit
        position
        heading
        tilt
        roll
        cam
        fig
    end
    
    methods
        function obj = Camera(environment, sight_range)
            %Camera A distorted perspective view of the insect field

            obj.E = environment;

            obj.sight = sight_range;

            obj.adjust_limit = 10;
            obj.position = obj.E.origin;

            obj.heading = 0;
            obj.tilt = 90;
            obj.roll = 0;

            obj.fig = figure();
            
            obj.cam = cameraIntrinsics([620,620],[500,500],[1000,1000]);
        end
        
        function adjust(obj, dt, delta_heading, delta_tilt)
            %adjust Nudge the camera orientation
            %  dt            Time step
            %  delta_heading Positive for clockwise; negative for anti-
            %  delta_tilt    Positive for up; negative for down
            %  Motion limit is 10 degrees per second

            limit = obj.adjust_limit * dt;

            if delta_heading > 0
                if delta_heading > limit
                    delta_heading = limit;
                end
                obj.heading = obj.heading + delta_heading;
                if obj.heading >= 360
                    obj.heading = obj.heading - 360;
                end
            elseif delta_heading < 0
                if (-delta_heading) > limit
                    delta_heading = -limit;
                end
                obj.heading = obj.heading + delta_heading;
                if obj.heading < 0
                    obj.heading = obj.heading + 360;
                end
            end
            if delta_tilt > 0
                if delta_tilt > limit
                    delta_tilt = limit;
                end
                obj.tilt = obj.tilt + delta_tilt;
                if obj.tilt >= 180
                    obj.tilt = 180;
                end
            elseif delta_tilt < 0
                if (-delta_tilt) > limit
                    delta_tilt = -limit;
                end
                obj.tilt = obj.tilt + delta_tilt;
                if obj.tilt < 0
                    obj.tilt = 0;
                end
            end
        end
        
        function targets = snap(obj)
            %snap Update bird position and orientation; look for insects.

            figure(obj.fig)
            cla()
            hold on
            axis([-1.6,1.6,-1.6,1.6])
            text(-1.5, 1.4, 'Heading:')
            text(-1.5, 1.2, 'Tilt:')
            text(-1.0, 1.4, num2str(obj.heading))
            text(-1.0, 1.2, num2str(obj.tilt))

            targets = [];
            insects = obj.E.subset(obj.position, obj.sight);
            if ~isempty(insects)
                insects = insects(insects(:,4) <= obj.sight,:);
            end
            rows = size(insects, 1);
            if rows > 0
                c = cosd(obj.heading);
                s = sind(obj.heading);
                h_mat = [s,-c,0;c,s,0;0,0,1];
                c = cosd(obj.tilt);
                s = sind(obj.tilt);
                t_mat = [1,0,0;0,s,c;0,-c,s];
                insects(:,1:3) = (insects(:,1:3) - obj.position()) * h_mat * t_mat; % TODO: check order
                insects = insects(insects(:,2) > 0,:);
            end
            rows = size(insects, 1);
            if rows > 0
                targets = zeros(rows, 3);
                m_set = ['^', 'v', '<', '>'];
                p_mat = [1,0,0;0,0,1;0,1,0];
            end
            for row = 1:rows
                rel_pos = insects(row,1:3) * p_mat;
                r = insects(row,4); % distance to insect
                p = worldToImage(obj.cam, eye(3), [0,0,0], rel_pos * 1000);
                xy = atan((p-500)/500); % +/- pi/2
                plot(xy(1), xy(2), 'Marker', m_set(randi(4)), 'MarkerSize',(25-r))
                targets(row,:) = [round(xy(1), 2), round(xy(2), 2), round(r, 2)];
            end
        end
    end
    
    methods(Static)
        function demo()
            E = Environment(60, 500, false);
            C = Camera(E, 20);

            dt = 0.1; % time-step [s]
            while ishandle(C.fig)
                E.update(dt);

                delta_heading = 1; % change in heading: compass direction 0-359 degrees
                delta_tilt    = 1; % change in tilt:    0 = down; 90 = level; 180 = up
                C.adjust(dt, delta_heading, delta_tilt);

                targets = C.snap();
                % targets is a matrix where each row represents an insect and the
                % three columns are X, Y, R, where R is the distance to the insect

                pause(dt)
            end
        end
    end
end

