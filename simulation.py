import time
from collections import defaultdict
import random
import networkx as nx
from person import Person

class Simulation:
    def __init__(self, city, people):
        self.city = city
        self.people = people
        self.time = 7 * 60  # 07:00
        self.end_time = 19 * 60  # 19:00
        self.occupancy = defaultdict(list)
        self.edge_traffic = defaultdict(int)
    def tick(self):
        self.occupancy.clear()
        self.edge_traffic.clear()

        # First pass: count traffic for congestion calculation
        for p in self.people:
            if p.current_path and p.current_index < len(p.current_path) - 1:
                current_node = p.current_path[p.current_index]
                next_node = p.current_path[p.current_index + 1]
                edge = tuple(sorted([current_node, next_node]))
                self.edge_traffic[edge] += 1

        # Update road traffic statistics
        self.city.update_road_traffic(self.edge_traffic)

        # Share traffic info with people for congestion decisions
        for p in self.people:
            p._current_traffic = self.edge_traffic

        # Second pass: move people
        for p in self.people:
            old = p.current_location()
            p.step(self.time)
            new = p.current_location()

            loc = p.current_location()
            self.occupancy[loc].append(p)

        self.time += 5

    def run(self):
        while self.time < self.end_time:
            self.tick()
            # original visualization would go here, but removed in headless mode
            time.sleep(0.1)

    def get_stats(self):
        return {
            'at_home': sum(p.state == 'at_home' for p in self.people),
            'at_work': sum(p.state == 'at_work' for p in self.people),
            'travelling': sum(p.is_traveling() for p in self.people),
            'visiting': sum(p.state == 'social_visit' for p in self.people),
            'shopping': sum(p.state == 'shop_visit' for p in self.people),
            'at_airport': sum(p.at_airport for p in self.people),  # New stat
        }

# -------------------------------------------------------------------
# NEW: WebSimulation subclass for Flask‑SocketIO integration
# -------------------------------------------------------------------
class WebSimulation(Simulation):
    def __init__(self, city, people, socketio, city_id, city_name):
        super().__init__(city, people)
        self.socketio = socketio
        self.city_id = city_id
        self.city_name = city_name

    def get_simulation_data(self):
        # --- build node list ---
        nodes = []
        for node in self.city.graph.nodes():
            node_type = self.city.node_type(node)
            is_subway = node in self.city.subway_nodes
            occupancy = len(self.occupancy.get(node, []))
            nodes.append({
                'id': node,
                'type': node_type,
                'occupancy': occupancy,
                'is_subway': is_subway
            })

        # --- build edge list ---
        edges = []
        for edge in self.city.graph.edges():
            key = tuple(sorted(edge))
            traffic = self.edge_traffic.get(key, 0)
            is_roadworks = self.city.is_roadworks(edge)
            edge_data = self.city.graph.get_edge_data(edge[0], edge[1])
            is_subway = edge_data.get('is_subway', False)
            edges.append({
                'source': edge[0],
                'target': edge[1],
                'traffic': traffic,
                'roadworks': is_roadworks,
                'is_subway': is_subway
            })

        # --- stats ---
        stats = self.get_stats()

        subway_loop = self.city.subway_nodes

        road_stats = self.city.get_road_stats()

        return {
            'cityId': self.city_id,
            'cityName': self.city_name,
            'time': f"{self.time//60:02}:{self.time%60:02}",
            'nodes': nodes,
            'edges': edges,
            'stats': stats,
            'subway_loop': subway_loop,
            'grid_positions': self.city.grid_positions,
            'road_stats': road_stats
        }

    def run(self):
        self.running = True
        try:
            while self.running and self.time < self.end_time:
                self.tick()
                data = self.get_simulation_data()
                self.socketio.emit('city_simulation_update', data)
                self.socketio.sleep(0.5)
        except Exception as e:
            print(f"[ERROR] Simulation thread crashed for {self.city_name}: {e}")

        if self.running:
            self.socketio.emit('city_simulation_completed', {'cityId': self.city_id})
        else:
            self.socketio.emit('city_simulation_stopped', {'cityId': self.city_id})