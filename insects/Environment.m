classdef Environment < handle
    %Environment Summary of this class goes here
    %   Detailed explanation goes here
    
    properties
        side    % length of cube side
        N       % number of insects
        data    % insect position/motion data
        origin  % cube center
        fig     % figure window, if requested
        pts     % plotted points
    end
    
    methods
        function obj = Environment(cube_side, insect_count, show_3D)
            %Environment Construct a periodic cube with insects
            if (nargin() < 3) % display cube by default
                show_3D = true;
            end
            obj.side = cube_side;
            obj.N = insect_count;
            obj.data = zeros(obj.N, 7);
            obj.origin = ones(1, 3) * obj.side / 2;

            obj.fig = [];
            obj.pts = [];

            % Give each insect a random speed between 0.25 and 1.25 m/s
            obj.data(:,1) = 0.25 + rand(obj.N, 1);
            % Give each insect a random initial position
            obj.data(:,2:4) = obj.side * rand(obj.N, 3);
            for row = 1:obj.N
                % Give each insect a random initial direction (unit vector)
                obj.data(row,5:7) = obj.random_unit_vector();
            end
            
            if show_3D
                obj.fig = figure();
                axis([0,1,0,1,0,1] * obj.side)
                box
                view(30, 30)
                xlabel('X [m]')
                ylabel('Y [m]')
                zlabel('Z [m]')
                obj.pts = plot3(obj.data(:,2), obj.data(:,3), obj.data(:,4), 'b.');
            end
        end
        
        function insects = subset(obj, center, radius)
            %subset Return subset of insects within containing cube
            insects = [];
            count = 0;
            for row = 1:obj.N
                r = [];
                for axis_z = -1:2
                    z = obj.data(row,4) + obj.side * axis_z;
                    for axis_y = -1:2
                        y = obj.data(row,3) + obj.side * axis_y;
                        for axis_x = -1:2
                            x = obj.data(row,2) + obj.side * axis_x;
                            r = obj.cube_check([x, y, z], center, radius);
                            if ~isempty(r)
                                break
                            end
                        end
                        if ~isempty(r)
                            break
                        end
                    end
                    if ~isempty(r)
                        break
                    end
                end
                if ~isempty(r)
                    if r(1) <= radius
                        count = count + 1;
                        insects(count,:) = [x, y, z, r(1)];
                    end
                end
            end
        end
        
        function update(obj, dt)
            %update Update the insect positions and directions of flight

            % update insect positions
            % newpos = obj.data(:,2:4) + (obj.data(:,5:7)' * obj.data(:,1))' * dt;
            newpos = obj.data(:,2:4) + (obj.data(:,5:7) .* obj.data(:,1)) * dt;
            newpos(:,1) = obj.wrap(newpos(:,1), obj.side);
            newpos(:,2) = obj.wrap(newpos(:,2), obj.side);
            newpos(:,3) = obj.wrap(newpos(:,3), obj.side);
            obj.data(:,2:4) = newpos;
            
            % update insect directions
            obj.data(:,5:7) = obj.nudge(obj.data(:,5:7), dt);

            % update 3D plot, if it was requested & created
            if ishandle(obj.fig)
                set(obj.pts, 'XData', newpos(:,1), 'YData', newpos(:,2), 'ZData', newpos(:,3));
                drawnow
            end
        end
    end
    
    methods(Static)
        function vec = random_unit_vector()
            mag = 0;
            while mag < 1E-15
                vec = random('Normal', 0, 1, 1, 3);
                mag = norm(vec);
            end
            vec = vec / mag;
        end
        function r = cube_check(xyz, center, radius)
            r = [];
            xyz = xyz - center;
            if max(abs(xyz)) <= radius
                r = norm(xyz);
            end
        end
        function direction = nudge(direction, weight)
            rows = size(direction, 1);
            for row = 1:rows
                new_direction = direction(row,:) * (1 - weight) + weight * Environment.random_unit_vector();
                direction(row,:) = new_direction / norm(new_direction);
            end
        end
        function coordinate = wrap(coordinate, side)
            for index = 1:length(coordinate)
                if coordinate(index) >= side
                    coordinate(index) = coordinate(index) - side;
                elseif coordinate(index) < 0
                    coordinate(index) = coordinate(index) + side;
                end
            end
        end
        function demo(cube_side, insect_count)
            E = Environment(cube_side, insect_count);
            while ishandle(E.fig)
                E.update(0.1);
                pause(0.1)
            end
        end
    end
end

