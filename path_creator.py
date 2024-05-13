import heapq
from math import sin, cos, pi

class Vertex:
    """
    Represents a Vertex in a graph.

    Attributes:
        x (float): x coordinate of the vertex.
        y (float): y coordinate of the vertex.
        prev (Vertex): The previous vertex in the path (if applicable).
        edges (list of Edge): The outgoing edges from this vertex.
        f_score (float): The cost to get to this vertex.
        club (str): The club used to get to this vertex in the path.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.prev = None
        self.edges = []
        self.f_score = float('inf')
        self.club = None

    def __lt__(self, other):
        """Defines comparison criteria for vertices, here being f_score.
        
        Args:
            other (Vertex): The vertex with which we want to compare.
        """
        return self.f_score < other.f_score
    
class Edge:
    """
    Represents an Edge in a graph.

    Attributes:
        end (Vertex): The endpoint of the edge.
        weight (float): The weight (cost) of the edge.
        club (str): The club used to create this edge.
    """
    def __init__(self, end, weight, club):
        self.end = end
        self.weight = weight
        self.club = club

class PathCreator:
    """
    Creates the graph and determines the shortest path from tee to pin.

    Attributes:
        course_width (float): The width of the course.
        course_length (float): The length of the course.
        hazards (list of (float, float)): The hazards on the course as tuples of (x,y) coordinates.
        start (Vertex): The starting vertex (tee).
        end (Vertex): The end vertex (pin).
        clubs (dict of {club (str):distance (float)}): Dictionary of club with their respective distances.
        wind (str): Strength of the wind (one of 'none':, 'moderate', 'high').
        fairway (list of (x (float),y (float))): Contains the (x,y) coordinates of the fairway.
        rough (list of (x (float),y (float))): Contains the (x,y) coordinates of the rough.
        bunker (list of (x (float),y (float))): Contains the (x,y) coordinates of the bunker.
    """
    def __init__(self, course_width, course_length, hazards, start, end, clubs, wind, fairway, rough, bunker):
        self.course_width = course_width
        self.course_length = course_length
        self.hazards = hazards 
        self.start = start
        self.end = end
        self.clubs = clubs
        self.wind = wind
        self.fairway = fairway
        self.rough = rough
        self.bunker = bunker
        self.vertices = [start] # Stores the vertices in the graph
        self.edges = [] # Stores the edges in the graph

    def make_graph(self, end, clubs):
        """
        Constructs the graph from the start, end and available clubs.

        Args:
            end (Vertex): The end vertex (pin).
            clubs (dict of {club (str):distance (float)}): Dictionary of club with their respective distances.
        """
        for curr_v in self.vertices: 
            num_vertices_added = 0
            for club, dist in clubs.items():
                # Skip this club if we were able to add >=3 vertices for a bigger club
                if num_vertices_added >= 3:
                    continue
                num_vertices_added = 0
                # Can reach pin with this shot
                if ((end.x-curr_v.x)**2 + (end.y-curr_v.y)**2)**0.5 <= dist:
                    x = self.end.x
                    y = self.end.y
                    h_prox = 0
                    num_obs = self.get_num_obs(curr_v.x, curr_v.y, x, y)
                    lie = self.get_lie(curr_v.x, curr_v.y)
                    new_weight = self.calc_weight(lie, self.wind, dist, num_obs, h_prox) 
                    curr_v.edges.append(Edge(end, new_weight, club))
                else:
                    spacing = 5 # Shots are 5 yards apart
                    theta = pi/2 # Start by looking for a straight shot
                    while theta < pi: # Look for shots to the left
                        x = curr_v.x + dist*cos(theta)
                        y = curr_v.y + dist*sin(theta)
                        if self.new_vertex_valid(x,y):
                            new_v = Vertex(x,y)  
                            h_prox = self.get_hazard_prox(x,y)
                            num_obs = self.get_num_obs(curr_v.x, curr_v.y, x, y)
                            lie = self.get_lie(curr_v.x, curr_v.y)
                            new_weight = self.calc_weight(lie, self.wind, dist, num_obs, h_prox) 
                            curr_v.edges.append(Edge(new_v, new_weight, club))
                            self.vertices.append(new_v)
                            num_vertices_added += 1
                        theta += spacing/dist
                    theta = pi/2
                    while theta > 0: # Look for shots to the right
                        x = curr_v.x + dist*cos(theta)
                        y = curr_v.y + dist*sin(theta)
                        if self.new_vertex_valid(x,y):
                            new_v = Vertex(x,y)  
                            h_prox = self.get_hazard_prox(x,y)
                            num_obs = self.get_num_obs(curr_v.x, curr_v.y, x, y)
                            lie = self.get_lie(curr_v.x, curr_v.y)
                            new_weight = self.calc_weight(lie, self.wind, dist, num_obs, h_prox) 
                            curr_v.edges.append(Edge(new_v, new_weight, club))
                            self.vertices.append(new_v)
                            num_vertices_added += 1
                        theta -= spacing/dist
        self.vertices.append(end)

    def calc_weight(self, lie, wind, club_dist, num_obs, prox_hazard):
        """
        Returns the weight of an edge (the g score), so the cost of a particular shot.

        Args:
            lie (str): The lie of the shot (one of 'rough', 'fairway', 'bunker').
            wind (str): Strength of the wind (one of 'none':, 'moderate', 'high').
            club_dist (float): The length of the shot.
            num_obs (int): The number of obstacles in the way of the shot.
            prox_hazard (float): The proximity of the landing point to a hazard.
        """
        lie_weights = {'rough':0.7, 'fairway':0.1, 'bunker':0.95}
        wind_weights = {'none':0.2, 'moderate':0.5, 'high':0.7}
        # Normalizing values
        norm_prox_hazard = prox_hazard/self.course_width
        norm_num_obs = num_obs/10
        norm_shot_dist = club_dist/(self.course_length**2+self.course_width**2)**0.5
        return 0.2*lie_weights[lie]+0.2*norm_shot_dist*wind_weights[wind] + 0.3*norm_num_obs + 0.3*norm_prox_hazard

    def new_vertex_valid(self, x, y):
        """
        Returns if a new vertex is valid (if it lands in the course not in a hazard).

        Args:
            x (float): The x value of the new vertex.
            y (float): The y value of the new vertex.
        """
        return y >= 0 and y <= self.course_width and x >=0 and x <= self.course_length and self.get_hazard_prox(x,y)>=1

    def get_hazard_prox(self, x1, y1):
        """
        Returns the proximity of a point to a hazard.

        Args:
            x1 (float): The x value of the point.
            y1 (float): The y value of the point.
        """
        # curr_min is initially out of bounds by width
        curr_min = min(y1, self.course_width-y1)
        for (x,y) in self.hazards:
            distance = ((x1 - x)**2 + (y1 - y)**2)**0.5
            if distance < curr_min:
                curr_min = distance
        return curr_min

    def get_num_obs(self, x1, y1, x2, y2):
        """
        Returns the number of obstacles (hazards) within the path of the shot.

        Args:
            x1 (float): The x value of the starting point.
            y1 (float): The y value of the starting point.
            x2 (float): The x value of the endpoint.
            y2 (float): The y value of the endpoint.
        """
        count = 0
        for (x,y) in self.hazards:
            slope = (y2-y1)/(x2-x1) if (x2 - x1) != 0 else float('inf')
            intercept = y1 - slope * x1
            if abs(y - (slope * x + intercept)) <= 1:
                count+=1
            if count == 10:
                break
        return count

    def get_lie(self, x, y):
        """Returns the lie of the shot (within 1 yard)
        
        Args:
            x (float): The x value of the point.
            y (float): The y value of the point.
        """
        for (x1,y1) in self.fairway:
            if ((x - x1)**2 + (y - y1)**2)**0.5 < 1:
                return 'fairway'
        for (x1,y1) in self.rough:
            if ((x - x1)**2 + (y - y1)**2)**0.5 < 1:
                return 'rough'
        for (x1,y1) in self.bunker:
            if ((x - x1)**2 + (y - y1)**2)**0.5 < 1:
                return 'bunker'
        return 'fairway'
    
    def run_search(self):
        """
        Runs the search for the shortest path.

        Returns:
            path (list of Vertex), clubs (list of str)
        """
        open_set = []
        self.start.f_score = 0
        heapq.heappush(open_set, self.start)  # (f_score, vertex)
    
        while open_set:
            current_vertex = heapq.heappop(open_set)
    
            if current_vertex == self.end: # Done search
                return self.reconstruct_path(self.end)
    
            for edge in current_vertex.edges:
                neighbour = edge.end
                g_score = current_vertex.f_score + edge.weight
                f_score = g_score + self.heuristic(neighbour, self.end)
                neighbour.f_score = f_score
                heapq.heappush(open_set, neighbour)
                neighbour.prev = current_vertex  # Update the predecessor
                neighbour.club = edge.club # Update the club
    
        return None  # No path found

    def heuristic(self, endpoint, pin):
        """
        Calculates the heuristic for an edge (the distance of the endpoint to the pin).

        Args:
            endpoint (Vertex): The end of the edge.
            pin (Vertex): The pin.
        
            Returns:
                The normalized distance between the two points.
        """
        max_dist = (self.course_width**2+self.course_length**2)**0.5
        return ((endpoint.x-pin.x)**2 + (endpoint.y-pin.y)**2)**0.5/max_dist

    def reconstruct_path(self, current):
        """
        Reconstructs the shortest path from the last vertex.

        Args:
            current (Vertex): The last vertex in the path.

        Returns: 
            path (list of Vertex), path_clubs (list of str)
        """
        path = []
        path_clubs = []
        while current:
            path.append(current)
            path_clubs.append(current.club)
            current = current.prev
        path.reverse()
        path_clubs.reverse()
        path_clubs = path_clubs[1:] # 1st vertex won't have a club
        return path, path_clubs