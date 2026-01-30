import random

class Person:
    def __init__(self, home, work, city):
        self.home = home
        self.work = work
        self.city = city
        # Precompute paths
        if work:
            self.morning_path = city.get_path(home, work)
            self.evening_path = list(reversed(self.morning_path)) if self.morning_path else None
        else:
            self.morning_path = None
            self.evening_path = None
        self.state = 'at_home'
        self.current_path = None
        self.current_index = 0
        self.in_visit = False
        self.social_visit_target = None
        self.social_visit_return_time = None
        self.shop_visit_target = None  # New: for shop visits
        self.shop_visit_return_time = None  # New: for shop visits
        self.at_airport = False  # New: for airport visits
        # Ensure evening commute only once
        self.evening_commuted = False
        self.congestion_delay = 0  # New: tracks congestion delays

    def step(self, current_time):
        hour = current_time // 60
        
        # If at airport, stay there for the rest of the day
        if self.at_airport:
            return
        
        # Handle congestion delay
        if self.congestion_delay > 0:
            self.congestion_delay -= 1
            return  # Skip movement this tick due to congestion
        
        # 1. Travel along existing path
        if self.current_path and self.current_index < len(self.current_path) - 1:
            # Check for congestion on next edge
            current_node = self.current_path[self.current_index]
            next_node = self.current_path[self.current_index + 1]
            
            # Get traffic count for this edge from simulation
            edge_key = tuple(sorted([current_node, next_node]))
            traffic_count = getattr(self, '_current_traffic', {}).get(edge_key, 0)
            
            # Apply congestion delay if traffic > 5
            if traffic_count > 5:
                self.congestion_delay = 1  # Wait one extra tick
                return
            
            self.current_index += 1
            if self.current_index == len(self.current_path) - 1:
                self._arrive()
            return

        # 2. Complete social visit return
        if self.state == 'social_visit' and self.in_visit and current_time >= self.social_visit_return_time:
            # return home after visit
            origin = self.social_visit_target
            dest = self.home
            return_path = self.city.get_path(origin, dest)
            if return_path:
                self._start_commute(return_path, 'commuting_home')
            self.in_visit = False
            self.social_visit_target = None
            return

        # 2b. Complete shop visit return
        if self.state == 'shop_visit' and self.in_visit and current_time >= self.shop_visit_return_time:
            # return home after shop visit
            origin = self.shop_visit_target
            dest = self.home
            return_path = self.city.get_path(origin, dest)
            if return_path:
                self._start_commute(return_path, 'commuting_home')
            self.in_visit = False
            self.shop_visit_target = None
            return

        # 3. Morning commute at 08:00
        if current_time == 8 * 60 and self.state == 'at_home' and self.work and self.morning_path:
            self._start_commute(self.morning_path, 'commuting_to_work')
            return

        # 4. Evening commute at or after 17:00 (only once)
        if current_time >= 17 * 60 and not self.evening_commuted and self.state == 'at_work' and not self.current_path and self.evening_path:
            self._start_commute(self.evening_path, 'commuting_home')
            self.evening_commuted = True
            return

        # 5. Airport visits - can happen at any time from home (2% chance per tick)
        if self.state == 'at_home' and not self.current_path and not self.in_visit and self.city.airport_nodes:
            if random.random() < 0.001:  # FIXED: Much lower chance (0.1% instead of 2%)
                self._start_airport_visit()
                return

        # 6. Shop visits between 9:00 and 19:00, but not during work hours for employed people
        if 9 <= hour < 19 and self.state == 'at_home' and not self.current_path and not self.in_visit:
            # Skip if person has work and it's work hours (8-17)
            if self.work and 8 <= hour < 17:
                pass  # Don't visit shops during work hours
            else:
                # 5% chance per tick for shop visit
                if random.random() < 0.05:
                    self._start_shop_visit(current_time)
                    return

        # 7. Random social visits between 10:00 and 16:00, only from home
        if 10 <= hour < 16 and self.state == 'at_home' and not self.current_path and not self.in_visit:
            # Skip if person has work and it's work hours
            if self.work and 8 <= hour < 17:
                pass  # Don't make social visits during work hours
            else:
                # 10% chance per tick
                if random.random() < 0.1:
                    self._start_social_visit(current_time)
                    return


    def _start_commute(self, path, new_state):
        self.state = new_state
        self.current_path = path
        self.current_index = 0

    def _start_social_visit(self, current_time):
        origin = self.home
        homes = [h for h in self.city.home_nodes if h != origin]
        target = random.choice(homes)
        path_to = self.city.get_path(origin, target)
        if not path_to:
            return
        travel_time = self.city.get_path_time(path_to)
        visit_duration = random.randint(30, 60)
        self.social_visit_return_time = current_time + travel_time + visit_duration
        self.state = 'social_visit'
        self.in_visit = True
        self.social_visit_target = target
        self.current_path = path_to
        self.current_index = 0

    def _start_shop_visit(self, current_time):
        if not self.city.shop_nodes:
            return
        origin = self.home
        target = random.choice(self.city.shop_nodes)
        path_to = self.city.get_path(origin, target)
        if not path_to:
            return
        travel_time = self.city.get_path_time(path_to)
        visit_duration = random.randint(15, 45)
        self.shop_visit_return_time = current_time + travel_time + visit_duration
        self.state = 'shop_visit'
        self.in_visit = True
        self.shop_visit_target = target
        self.current_path = path_to
        self.current_index = 0

    def _start_airport_visit(self):
        """Start a visit to the airport - person stays there for rest of day"""
        if not self.city.airport_nodes:
            return
        
        origin = self.home
        target = self.city.airport_nodes[0]  # There's only one airport
        path_to = self.city.get_path(origin, target)
        if not path_to:
            return
        
        self.state = 'traveling_to_airport'
        self.current_path = path_to
        self.current_index = 0

    def _arrive(self):
        loc = self.current_path[self.current_index]
        if self.state == 'commuting_to_work' and loc == self.work:
            self.state = 'at_work'
        elif self.state == 'commuting_home' and loc == self.home:
            self.state = 'at_home'
        elif self.state == 'traveling_to_airport' and loc in self.city.airport_nodes:
            self.state = 'at_airport'
            self.at_airport = True
        self.current_path = None
        self.current_index = 0

    def current_location(self):
        if self.current_path:
            return self.current_path[self.current_index]
        if self.at_airport:
            return self.city.airport_nodes[0] if self.city.airport_nodes else self.home
        return self.home if self.state in ['at_home', 'social_visit', 'shop_visit'] else (self.work or self.home)

    def is_traveling(self):
        return self.current_path is not None