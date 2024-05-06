import heapq
from math import sin, cos, pi

class Vertex:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.prev = None
        self.edges = []
        self.f_score = float('inf')
        self.club = None

    def __lt__(self, other):
        return self.f_score < other.f_score
    
class Edge:
    def __init__(self, end, weight, club):
        self.end = end
        self.weight = weight
        self.club = club

class PathCreator:
    def __init__(self, course_width, course_length, hazards, start, end, clubs, wind, fairway, rough, bunker):
        self.course_width = course_width
        self.course_length = course_length
        self.hazards = hazards #{water:[x,y,w,h]}
        self.start = start
        self.end = end
        self.clubs = clubs
        self.vertices = [start]
        self.edges = []
        self.wind = wind
        self.fairway = fairway
        self.rough = rough
        self.bunker = bunker

    def make_graph(self, start, end, clubs):
        for curr_v in self.vertices: 
            num_vertices_added = 0
            for club, dist in clubs.items():
                # Skip this club if we were able to add >=3 vertices for a bigger club
                if num_vertices_added >= 3:
                    continue
                num_vertices_added = 0
                if ((end.x-curr_v.x)**2 + (end.y-curr_v.y)**2)**0.5 <= dist:
                    x = self.end.x
                    y = self.end.y
                    h_prox = 0
                    num_obs = self.get_num_obs(curr_v.x, curr_v.y, x, y)
                    lie = self.get_lie(curr_v.x, curr_v.y)
                    new_weight = self.calc_weight(lie, self.wind, dist, num_obs, h_prox) 
                    curr_v.edges.append(Edge(end, new_weight, club))
                else:
                    spacing = 5 # 2 yards apart
                    theta = 0
                    while theta < pi:
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
        self.vertices.append(end)

    
    def calc_weight(self, lie, wind, club_dist, num_obs, prox_hazard):
        lie_weights = {'rough':0.7, 'fairway':0.5, 'bunker':0.95}
        wind_weights = {'none':0.2, 'moderate':0.5, 'high':0.7}
        #TODO: does this make sense
        norm_shot_dist = club_dist/self.course_length
        norm_num_obs = num_obs
        norm_prox_hazard = prox_hazard
        return 0.3*lie_weights[lie]+0.2*norm_shot_dist*wind_weights[wind] + 0.4*norm_num_obs + 0.1*norm_prox_hazard

    def new_vertex_valid(self, x, y):
        return y >= 0 and y <= self.course_width and x >=0 and x <= self.course_length and self.get_hazard_prox(x,y)>=1

    def get_hazard_prox(self, x1, y1):
        curr_min = float('inf')
        for (x,y) in self.hazards:
            distance = ((x1 - x)**2 + (y1 - y)**2)**0.5
            if distance < curr_min:
                curr_min = distance
        return curr_min

    def get_num_obs(self, x1, y1, x2, y2):
        count = 0
        for (x,y) in self.hazards:
            slope = (y2-y1)/(x2-x1) if (x2 - x1) != 0 else float('inf')
            intercept = y1 - slope * x1
            if abs(y - (slope * x + intercept)) <= 1:
                count+=1
        return count

    def get_lie(self, x, y):
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
        open_set = []
        self.start.f_score = 0
        heapq.heappush(open_set, self.start)  # (f_score, vertex)
    
        while open_set:
            current_vertex = heapq.heappop(open_set)
    
            if current_vertex == self.end:
                return self.reconstruct_path(self.end)
    
            for edge in current_vertex.edges:
                neighbour = edge.end
                g_score = current_vertex.f_score + edge.weight
                f_score = g_score + self.heuristic(neighbour, self.end)
                neighbour.f_score = f_score
                heapq.heappush(open_set, neighbour)
                neighbour.prev = current_vertex  # Update the predecessor
                neighbour.club = edge.club
    
        return None  # No path found

    def heuristic(self, start, end):
        max_dist = (self.course_width**2+self.course_length**2)**0.5
        return ((start.x-end.x)**2 + (start.y-end.y)**2)**0.5

    def reconstruct_path(self, current):
        path = []
        path_clubs = []
        while current:
            path.append(current)
            path_clubs.append(current.club)
            current = current.prev
        path.reverse()
        path_clubs.reverse()
        path_clubs = path_clubs[1:] #1st vertex won't have a club
        return path, path_clubs