import networkx as nx
import random
import math

class City:
    def __init__(self, home_count=40, work_count=20, subway_count=5, image_positions=None):
        self.graph = nx.Graph()
        self.home_nodes = []
        self.work_nodes = []
        self.shop_nodes = []
        self.subway_nodes = []
        self.apartment_nodes = []  # New: apartment nodes
        self.airport_nodes = []    # New: airport nodes
        self.home_count = home_count
        self.work_count = work_count
        self.shop_count = (home_count + work_count) // 4
        self.subway_count = subway_count
        self.roadworks = set()
        self.grid_positions = {}  # Store grid coordinates for each node
        self.roads = {}  # Store road information
        self.image_positions = image_positions  # New: positions from uploaded image
        self._build_city()
        self._initialize_roadworks()
        self._identify_roads()

    def _build_city(self):
        if self.image_positions:
            self._build_city_from_image()
        else:
            self._build_city_default()

    def _build_city_from_image(self):
        """Build city layout based on uploaded image positions"""
        print(f"[DEBUG] Building city from image with {len(self.image_positions)} positions")
        
        # Get all available positions from the image
        available_positions = list(self.image_positions.values())
        total_nodes = self.home_count + self.work_count + self.shop_count
        
        # Check if we need apartments and airport
        has_apartments = total_nodes > 100
        has_airport = total_nodes > 100
        
        if has_airport:
            total_nodes += 1  # Add one airport node
        
        # If we have fewer positions than nodes, we'll need to adapt
        if len(available_positions) < total_nodes:
            print(f"[WARNING] Image has {len(available_positions)} positions but need {total_nodes} nodes")
            # Fill remaining positions with nearby grid positions
            self._expand_positions_grid(available_positions, total_nodes)
        
        # Shuffle positions for random distribution
        random.shuffle(available_positions)
        
        # Calculate center for zoning
        if available_positions:
            center_row = sum(pos[0] for pos in available_positions) / len(available_positions)
            center_col = sum(pos[1] for pos in available_positions) / len(available_positions)
        else:
            center_row = center_col = 0
        
        # Sort positions by distance from center for zoning
        def distance_from_center(pos):
            return math.sqrt((pos[0] - center_row)**2 + (pos[1] - center_col)**2)
        
        sorted_positions = sorted(available_positions, key=distance_from_center)
        
        # Allocate positions: work in center, homes on periphery, shops mixed
        work_positions = sorted_positions[:self.work_count]
        remaining_positions = sorted_positions[self.work_count:]
        
        # Mix homes and shops in remaining positions
        home_shop_positions = remaining_positions[:self.home_count + self.shop_count]
        random.shuffle(home_shop_positions)
        
        home_positions = home_shop_positions[:self.home_count]
        shop_positions = home_shop_positions[self.home_count:self.home_count + self.shop_count]
        
        # Create nodes
        for i, pos in enumerate(work_positions):
            node = f"W{i}"
            self.graph.add_node(node, type='work')
            self.work_nodes.append(node)
            self.grid_positions[node] = pos
        
        for i, pos in enumerate(home_positions):
            node = f"H{i}"
            self.graph.add_node(node, type='home')
            self.home_nodes.append(node)
            self.grid_positions[node] = pos
        
        for i, pos in enumerate(shop_positions):
            node = f"S{i}"
            self.graph.add_node(node, type='shop')
            self.shop_nodes.append(node)
            self.grid_positions[node] = pos
        
        # Convert homes to apartments if city is large enough
        if has_apartments:
            self._convert_homes_to_apartments(center_row, center_col)
        
        # Add airport if city is large enough
        if has_airport:
            self._add_airport(available_positions, center_row, center_col)
        
        # Create connections with proper limits (max 4 per node)
        self._create_limited_connections()
        
        # Select subway nodes
        potential_subway_nodes = self.work_nodes + self.shop_nodes
        if self.subway_count > len(potential_subway_nodes):
            self.subway_count = len(potential_subway_nodes)
        self.subway_nodes = random.sample(potential_subway_nodes, self.subway_count)
        
        # Connect subway nodes in a loop
        if len(self.subway_nodes) >= 3:
            for i in range(len(self.subway_nodes)):
                node1 = self.subway_nodes[i]
                node2 = self.subway_nodes[(i+1) % len(self.subway_nodes)]
                self.graph.add_edge(node1, node2, weight=2, is_subway=True)

    def _create_limited_connections(self):
        """Create connections between nearby nodes with a maximum of 4 connections per node"""
        nodes = list(self.grid_positions.keys())
        connection_count = {node: 0 for node in nodes}
        MAX_CONNECTIONS = 4
        
        # Calculate all possible connections with distances
        potential_connections = []
        
        for i, node1 in enumerate(nodes):
            pos1 = self.grid_positions[node1]
            
            for j, node2 in enumerate(nodes[i+1:], i+1):
                pos2 = self.grid_positions[node2]
                distance = math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                
                # Only consider reasonable distances (adjust threshold as needed)
                if distance <= 3.0:  # Slightly larger threshold for image-based layouts
                    potential_connections.append((distance, node1, node2))
        
        # Sort by distance (shortest first) to prioritize closer connections
        potential_connections.sort()
        
        # Add connections respecting the maximum limit
        for distance, node1, node2 in potential_connections:
            if (connection_count[node1] < MAX_CONNECTIONS and 
                connection_count[node2] < MAX_CONNECTIONS):
                
                self.graph.add_edge(node1, node2, weight=5)
                connection_count[node1] += 1
                connection_count[node2] += 1
        
        # Ensure all nodes have at least one connection (connect isolated nodes)
        for node in nodes:
            if connection_count[node] == 0:
                # Find the closest node that can accept another connection
                pos = self.grid_positions[node]
                closest_candidates = []
                
                for other_node in nodes:
                    if (other_node != node and 
                        connection_count[other_node] < MAX_CONNECTIONS and
                        not self.graph.has_edge(node, other_node)):
                        
                        other_pos = self.grid_positions[other_node]
                        distance = math.sqrt((pos[0] - other_pos[0])**2 + (pos[1] - other_pos[1])**2)
                        closest_candidates.append((distance, other_node))
                
                if closest_candidates:
                    closest_candidates.sort()
                    closest_node = closest_candidates[0][1]
                    self.graph.add_edge(node, closest_node, weight=5)
                    connection_count[node] += 1
                    connection_count[closest_node] += 1
        
        # Log connection statistics for debugging
        avg_connections = sum(connection_count.values()) / len(connection_count)
        max_connections = max(connection_count.values())
        print(f"[DEBUG] Connection stats - Average: {avg_connections:.1f}, Maximum: {max_connections}")

    def _expand_positions_grid(self, positions, needed_count):
        """Expand available positions using grid-based approach"""
        if not positions:
            return
        
        # Find bounds of existing positions
        min_row = min(pos[0] for pos in positions)
        max_row = max(pos[0] for pos in positions)
        min_col = min(pos[1] for pos in positions)
        max_col = max(pos[1] for pos in positions)
        
        # Add adjacent grid positions until we have enough
        existing_positions = set(positions)
        
        while len(positions) < needed_count:
            new_positions = []
            
            # For each existing position, try to add adjacent positions
            for row, col in list(positions):
                adjacent = [
                    (row-1, col), (row+1, col),
                    (row, col-1), (row, col+1)
                ]
                
                for adj_pos in adjacent:
                    if adj_pos not in existing_positions:
                        new_positions.append(adj_pos)
                        existing_positions.add(adj_pos)
                        
                        if len(positions) + len(new_positions) >= needed_count:
                            break
                
                if len(positions) + len(new_positions) >= needed_count:
                    break
            
            if not new_positions:
                break  # No more adjacent positions available
            
            positions.extend(new_positions[:needed_count - len(positions)])

    def _build_city_default(self):
        # Calculate grid size based on total nodes
        total_nodes = self.home_count + self.work_count + self.shop_count
        
        # Check if we need apartments and airport
        has_apartments = total_nodes > 100
        has_airport = total_nodes > 100
        
        if has_airport:
            total_nodes += 1  # Add one airport node
            
        grid_size = math.ceil(math.sqrt(total_nodes * 1.3))
        # Create all grid positions
        all_positions = [(row, col) for row in range(grid_size) for col in range(grid_size)]
        
        # Define zones with more realistic boundaries
        center_radius = grid_size // 4  # Work zone is smaller, more concentrated
        home_inner_radius = grid_size // 3  # Homes start closer to center
        home_outer_radius = grid_size // 2  # Homes extend further out
        
        center_x, center_y = grid_size // 2, grid_size // 2
        
        # Categorize positions by distance from center
        work_positions = []
        home_positions = []
        mixed_positions = []  # For interspersing shops
        
        for row, col in all_positions:
            distance_from_center = math.sqrt((row - center_x)**2 + (col - center_y)**2)
            
            if distance_from_center <= center_radius:
                # Core area: mix of work and shops
                work_positions.append((row, col))
            elif distance_from_center <= home_inner_radius:
                # Inner residential: mix of homes and shops
                mixed_positions.append((row, col))
            elif distance_from_center <= home_outer_radius:
                # Outer residential: mostly homes with some shops
                home_positions.append((row, col))
        
        # Shuffle all position lists for randomization
        random.shuffle(work_positions)
        random.shuffle(home_positions)
        random.shuffle(mixed_positions)
        
        # Place work nodes in core area, with some shops interspersed
        work_to_place = min(self.work_count, len(work_positions))
        shops_in_core = min(self.shop_count // 3, len(work_positions) - work_to_place)
        
        # Place work nodes
        for i in range(work_to_place):
            pos = work_positions[i]
            node = f"W{i}"
            self.graph.add_node(node, type='work')
            self.work_nodes.append(node)
            self.grid_positions[node] = pos
        
        # Place some shops in core area
        shops_placed = 0
        for i in range(work_to_place, work_to_place + shops_in_core):
            if i < len(work_positions) and shops_placed < self.shop_count:
                pos = work_positions[i]
                node = f"S{shops_placed}"
                self.graph.add_node(node, type='shop')
                self.shop_nodes.append(node)
                self.grid_positions[node] = pos
                shops_placed += 1
        
        # Place homes in outer areas with shops interspersed
        all_home_positions = home_positions + mixed_positions
        random.shuffle(all_home_positions)
        
        homes_to_place = min(self.home_count, len(all_home_positions))
        remaining_shops = self.shop_count - shops_placed
        
        # Intersperse homes and shops
        combined_residential = []
        for i in range(homes_to_place):
            combined_residential.append(('home', i))
        
        # Add remaining shops distributed among homes
        shop_interval = max(1, homes_to_place // max(1, remaining_shops))
        for i in range(remaining_shops):
            insert_pos = min((i + 1) * shop_interval, len(combined_residential))
            combined_residential.insert(insert_pos, ('shop', shops_placed + i))
        
        # Place nodes according to the mixed list
        for idx, (node_type, type_idx) in enumerate(combined_residential):
            if idx >= len(all_home_positions):
                break
                
            pos = all_home_positions[idx]
            
            if node_type == 'home' and type_idx < self.home_count:
                node = f"H{type_idx}"
                self.graph.add_node(node, type='home')
                self.home_nodes.append(node)
                self.grid_positions[node] = pos
            elif node_type == 'shop' and type_idx < self.shop_count:
                node = f"S{type_idx}"
                self.graph.add_node(node, type='shop')
                self.shop_nodes.append(node)
                self.grid_positions[node] = pos
        
        # Convert homes to apartments if city is large enough
        if has_apartments:
            self._convert_homes_to_apartments(center_x, center_y)
        
        # Add airport if city is large enough
        if has_airport:
            self._add_airport_default(grid_size, center_x, center_y)
        
        # Create grid connections (each node connects to up to 4 neighbors)
        self._create_grid_connections()
        
        # Select subway nodes randomly from work and shop nodes
        potential_subway_nodes = self.work_nodes + self.shop_nodes
        if self.subway_count > len(potential_subway_nodes):
            self.subway_count = len(potential_subway_nodes)
        self.subway_nodes = random.sample(potential_subway_nodes, self.subway_count)
        
        # Connect subway nodes in a loop (separate from grid connections)
        if len(self.subway_nodes) >= 3:
            for i in range(len(self.subway_nodes)):
                node1 = self.subway_nodes[i]
                node2 = self.subway_nodes[(i+1) % len(self.subway_nodes)]
                self.graph.add_edge(node1, node2, weight=2, is_subway=True)

    def _convert_homes_to_apartments(self, center_row, center_col):
        """Convert 20% of homes closest to center into apartments"""
        if not self.home_nodes:
            return
        
        # Calculate distances from center for all homes
        home_distances = []
        for home in self.home_nodes:
            pos = self.grid_positions[home]
            distance = math.sqrt((pos[0] - center_row)**2 + (pos[1] - center_col)**2)
            home_distances.append((distance, home))
        
        # Sort by distance and take closest 20%
        home_distances.sort()
        num_apartments = max(1, len(self.home_nodes) // 5)  # 20% of homes
        
        for i in range(num_apartments):
            if i < len(home_distances):
                _, home_node = home_distances[i]
                
                # Convert home to apartment
                self.graph.nodes[home_node]['type'] = 'apartment'
                self.apartment_nodes.append(home_node)
                self.home_nodes.remove(home_node)
                
                print(f"[DEBUG] Converted {home_node} to apartment")

    def _add_airport(self, available_positions, center_row, center_col):
        """Add airport at edge of city for image-based layout"""
        # Find position furthest from center
        edge_positions = []
        for pos in available_positions:
            if pos not in self.grid_positions.values():  # Not already used
                distance = math.sqrt((pos[0] - center_row)**2 + (pos[1] - center_col)**2)
                edge_positions.append((distance, pos))
        
        if edge_positions:
            # Sort by distance (furthest first) and take the furthest position
            edge_positions.sort(reverse=True)
            airport_pos = edge_positions[0][1]
            
            node = "AIRPORT"
            self.graph.add_node(node, type='airport')
            self.airport_nodes.append(node)
            self.grid_positions[node] = airport_pos
            
            self._connect_airport_to_network(node, airport_pos)
            
            print(f"[DEBUG] Added airport at position {airport_pos}")
    
    def _add_airport_default(self, grid_size, center_x, center_y):
        """Add airport at edge of city for default layout"""
        # Place airport at one of the corners (furthest from center)
        corner_positions = [
            (0, 0), (0, grid_size-1), 
            (grid_size-1, 0), (grid_size-1, grid_size-1)
        ]
        
        # Find corner furthest from any existing node
        best_pos = None
        max_min_distance = 0
        
        for corner in corner_positions:
            if corner not in self.grid_positions.values():
                # Calculate minimum distance to any existing node
                min_distance = float('inf')
                for existing_pos in self.grid_positions.values():
                    distance = math.sqrt((corner[0] - existing_pos[0])**2 + (corner[1] - existing_pos[1])**2)
                    min_distance = min(min_distance, distance)
                
                if min_distance > max_min_distance:
                    max_min_distance = min_distance
                    best_pos = corner
        
        if best_pos:
            node = "AIRPORT"
            self.graph.add_node(node, type='airport')
            self.airport_nodes.append(node)
            self.grid_positions[node] = best_pos
            
            # FIXED: Connect airport to nearby nodes
            self._connect_airport_to_network(node, best_pos)
            
            print(f"[DEBUG] Added airport at position {best_pos}")
    
    def _connect_airport_to_network(self, airport_node, airport_pos):
        """Connect airport to the nearest 1-2 nodes in the city network"""
        # Find the closest nodes to connect to
        distances = []
        for node, pos in self.grid_positions.items():
            if node != airport_node:  # Don't connect to itself
                distance = math.sqrt((airport_pos[0] - pos[0])**2 + (airport_pos[1] - pos[1])**2)
                distances.append((distance, node))
        
        # Sort by distance and connect to the 1-2 closest nodes
        distances.sort()
        connections_made = 0
        max_connections = 2  # Connect to at most 2 nodes
        
        for distance, node in distances:
            if connections_made >= max_connections:
                break
            
            # Only connect if distance is reasonable (not too far)
            if distance <= 5.0:
                self.graph.add_edge(airport_node, node, weight=5)
                connections_made += 1
                print(f"[DEBUG] Connected airport to {node} (distance: {distance:.2f})")
        
        if connections_made == 0:
            print(f"[WARNING] Could not connect airport to any nearby nodes")

    def _create_grid_connections(self):
        """Create grid-based connections between adjacent nodes (max 4 per node)"""
        # Create a mapping from grid position to node
        pos_to_node = {pos: node for node, pos in self.grid_positions.items()}
        
        # For each node, connect to adjacent grid positions
        for node, (row, col) in self.grid_positions.items():
            # Check all 4 directions: up, down, left, right
            adjacent_positions = [
                (row-1, col),  # up
                (row+1, col),  # down
                (row, col-1),  # left
                (row, col+1)   # right
            ]
            
            connections = 0
            for adj_pos in adjacent_positions:
                if adj_pos in pos_to_node and connections < 4:
                    neighbor = pos_to_node[adj_pos]
                    # Add edge if it doesn't exist (undirected graph)
                    if not self.graph.has_edge(node, neighbor):
                        self.graph.add_edge(node, neighbor, weight=5)
                        connections += 1

    def _initialize_roadworks(self):
        """Initialize some random roadworks (5-10% of edges)"""
        # Only consider non-subway edges for roadworks
        non_subway_edges = [edge for edge in self.graph.edges() 
                           if not self.graph.get_edge_data(edge[0], edge[1]).get('is_subway', False)]
        num_roadworks = max(1, len(non_subway_edges) // 15)
        roadwork_edges = random.sample(non_subway_edges, num_roadworks)
        for edge in roadwork_edges:
            self.roadworks.add(tuple(sorted(edge)))

    def get_path(self, start, end):
        """Get shortest path avoiding roadworks, considering edge weights"""
        try:
            temp_graph = self.graph.copy()
            for edge in self.roadworks:
                if temp_graph.has_edge(edge[0], edge[1]):
                    temp_graph.remove_edge(edge[0], edge[1])
            
            return nx.shortest_path(temp_graph, start, end, weight='weight')
        except nx.NetworkXNoPath:
            return None
    
    def get_path_time(self, path):
        """Calculate total travel time for a path"""
        if not path or len(path) < 2:
            return 0
        total_time = 0
        for i in range(len(path) - 1):
            edge_data = self.graph.get_edge_data(path[i], path[i+1])
            total_time += edge_data.get('weight', 5)
        return total_time

    def is_roadworks(self, edge):
        """Check if an edge has roadworks"""
        return tuple(sorted(edge)) in self.roadworks

    def node_type(self, node):
        return self.graph.nodes[node]['type']
    
    def _identify_roads(self):
        """Identify and name road segments based on grid layout"""
        self.roads = {}
        
        # Get all grid positions and find bounds
        if not self.grid_positions:
            return
            
        positions = list(self.grid_positions.values())
        min_row = min(pos[0] for pos in positions)
        max_row = max(pos[0] for pos in positions)
        min_col = min(pos[1] for pos in positions)
        max_col = max(pos[1] for pos in positions)
        
        # Create position to node mapping
        pos_to_node = {pos: node for node, pos in self.grid_positions.items()}
        
        # Identify horizontal roads (Streets) - same row, different columns
        street_num = 1
        for row in range(min_row, max_row + 1):
            nodes_in_row = []
            for col in range(min_col, max_col + 1):
                if (row, col) in pos_to_node:
                    nodes_in_row.append((col, pos_to_node[(row, col)]))
            
            if len(nodes_in_row) >= 2:
                # Sort by column and create road segments
                nodes_in_row.sort()
                road_name = f"{self._ordinal(street_num)} Street"
                edges = []
                
                for i in range(len(nodes_in_row) - 1):
                    node1 = nodes_in_row[i][1]
                    node2 = nodes_in_row[i + 1][1]
                    if self.graph.has_edge(node1, node2):
                        edges.append(tuple(sorted([node1, node2])))
                
                if edges:
                    self.roads[road_name] = {
                        'type': 'street',
                        'edges': edges,
                        'current_traffic': 0,
                        'peak_traffic': 0
                    }
                    street_num += 1
        
        # Identify vertical roads (Avenues) - same column, different rows
        avenue_num = 1
        for col in range(min_col, max_col + 1):
            nodes_in_col = []
            for row in range(min_row, max_row + 1):
                if (row, col) in pos_to_node:
                    nodes_in_col.append((row, pos_to_node[(row, col)]))
            
            if len(nodes_in_col) >= 2:
                # Sort by row and create road segments
                nodes_in_col.sort()
                road_name = f"{self._ordinal(avenue_num)} Avenue"
                edges = []
                
                for i in range(len(nodes_in_col) - 1):
                    node1 = nodes_in_col[i][1]
                    node2 = nodes_in_col[i + 1][1]
                    if self.graph.has_edge(node1, node2):
                        edges.append(tuple(sorted([node1, node2])))
                
                if edges:
                    self.roads[road_name] = {
                        'type': 'avenue',
                        'edges': edges,
                        'current_traffic': 0,
                        'peak_traffic': 0
                    }
                    avenue_num += 1

    def _ordinal(self, n):
        """Convert number to ordinal (1st, 2nd, 3rd, etc.)"""
        if 10 <= n % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"

    def update_road_traffic(self, edge_traffic):
        """Update current traffic for each road and track peak traffic"""
        for road_name, road_info in self.roads.items():
            current_traffic = 0
            for edge in road_info['edges']:
                current_traffic += edge_traffic.get(edge, 0)
            
            road_info['current_traffic'] = current_traffic
            road_info['peak_traffic'] = max(road_info['peak_traffic'], current_traffic)

    def get_road_stats(self):
        """Get road statistics for display"""
        return {name: {
            'type': info['type'],
            'current_traffic': info['current_traffic'],
            'peak_traffic': info['peak_traffic'],
            'edge_count': len(info['edges'])
        } for name, info in self.roads.items()}
