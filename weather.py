import random
import math

class WeatherSystem:
    """
    Manages dynamic weather conditions for a city.
    Weather changes throughout the day and affects traffic and roadworks.
    """
    
    WEATHER_TYPES = ['clear', 'rain', 'snow', 'heatwave']
    
    def __init__(self, city_name):
        self.city_name = city_name
        self.current_weather = 'clear'
        self.weather_duration = 0  # How long current weather lasts (in minutes)
        self.next_weather_change = random.randint(60, 180)  # When to change weather next
        self.weather_history = []
        
        # Initialize with random starting weather
        self._initialize_weather()
    
    def _initialize_weather(self):
        """Set initial weather conditions based on random chance"""
        weather_probabilities = {
            'clear': 0.5,
            'rain': 0.25,
            'snow': 0.15,
            'heatwave': 0.1
        }
        
        rand = random.random()
        cumulative = 0
        for weather, prob in weather_probabilities.items():
            cumulative += prob
            if rand <= cumulative:
                self.current_weather = weather
                break
        
        self.weather_duration = random.randint(60, 180)
        print(f"[WEATHER] {self.city_name} starting with {self.current_weather} weather")
    
    def update(self, current_time):
        """
        Update weather conditions based on time of day.
        Weather changes dynamically throughout the simulation.
        
        Args:
            current_time: Current simulation time in minutes since midnight
        """
        hour = current_time // 60
        
        # Check if it's time to change weather
        if self.weather_duration <= 0:
            self._change_weather(hour)
        
        self.weather_duration -= 5  # Decrease by tick duration
    
    def _change_weather(self, hour):
        """
        Change to a new weather condition based on time of day.
        Different weather types are more likely at different times.
        """
        # Time-based weather probabilities
        if 6 <= hour < 10:  # Morning
            probabilities = {
                'clear': 0.4,
                'rain': 0.3,
                'snow': 0.2,
                'heatwave': 0.1
            }
        elif 10 <= hour < 14:  # Midday
            probabilities = {
                'clear': 0.3,
                'rain': 0.2,
                'snow': 0.1,
                'heatwave': 0.4  # Heatwaves more likely during midday
            }
        elif 14 <= hour < 18:  # Afternoon
            probabilities = {
                'clear': 0.35,
                'rain': 0.35,
                'snow': 0.15,
                'heatwave': 0.15
            }
        else:  # Evening
            probabilities = {
                'clear': 0.5,
                'rain': 0.25,
                'snow': 0.2,
                'heatwave': 0.05
            }
        
        # Select new weather
        rand = random.random()
        cumulative = 0
        new_weather = 'clear'
        
        for weather, prob in probabilities.items():
            cumulative += prob
            if rand <= cumulative:
                new_weather = weather
                break
        
        # Don't change to the same weather
        if new_weather == self.current_weather:
            # Pick a different weather type
            other_weathers = [w for w in self.WEATHER_TYPES if w != self.current_weather]
            new_weather = random.choice(other_weathers)
        
        old_weather = self.current_weather
        self.current_weather = new_weather
        self.weather_duration = random.randint(60, 240)  # Weather lasts 1-4 hours
        
        self.weather_history.append({
            'time': hour,
            'from': old_weather,
            'to': new_weather
        })
        
        print(f"[WEATHER] {self.city_name} weather changed from {old_weather} to {new_weather} at {hour:02d}:00")
    
    def get_congestion_multiplier(self):
        """
        Get the congestion multiplier based on current weather.
        Rain increases congestion effects.
        
        Returns:
            float: Multiplier for congestion threshold (lower = more congestion)
        """
        if self.current_weather == 'rain':
            return 0.6  # Rain makes congestion worse (traffic jams at lower counts)
        elif self.current_weather == 'snow':
            return 0.7  # Snow also increases congestion
        return 1.0
    
    def get_transit_time_multiplier(self):
        """
        Get the transit time multiplier based on current weather.
        Snow doubles transit times.
        
        Returns:
            float: Multiplier for edge weights/transit times
        """
        if self.current_weather == 'snow':
            return 2.0  # Snow doubles transit time
        elif self.current_weather == 'rain':
            return 1.3  # Rain increases transit time by 30%
        return 1.0
    
    def get_roadworks_multiplier(self):
        """
        Get the roadworks multiplier based on current weather.
        Heatwaves increase roadwork activity.
        
        Returns:
            float: Multiplier for roadworks probability
        """
        if self.current_weather == 'heatwave':
            return 2.0  # Heatwaves double roadwork activity
        elif self.current_weather == 'rain':
            return 0.5  # Rain reduces roadwork activity
        return 1.0
    
    def should_add_roadworks(self):
        """
        Determine if new roadworks should be added based on weather.
        Heatwaves increase roadwork probability.
        
        Returns:
            bool: True if roadworks should be added
        """
        base_probability = 0.02  # 2% base chance per update
        multiplier = self.get_roadworks_multiplier()
        
        return random.random() < (base_probability * multiplier)
    
    def should_remove_roadworks(self):
        """
        Determine if roadworks should be removed.
        
        Returns:
            bool: True if roadworks should be removed
        """
        base_probability = 0.05  # 5% base chance per update
        
        # Rain increases roadwork removal (work stops)
        if self.current_weather == 'rain':
            return random.random() < (base_probability * 2.0)
        
        return random.random() < base_probability
    
    def get_weather_info(self):
        """
        Get current weather information for display.
        
        Returns:
            dict: Weather information including type and effects
        """
        effects = []
        
        if self.current_weather == 'rain':
            effects.append("Increased congestion")
            effects.append("+30% travel time")
        elif self.current_weather == 'snow':
            effects.append("Doubled travel time")
            effects.append("Increased congestion")
        elif self.current_weather == 'heatwave':
            effects.append("Increased roadworks")
        else:
            effects.append("Normal conditions")
        
        return {
            'type': self.current_weather,
            'duration_remaining': max(0, self.weather_duration),
            'effects': effects,
            'congestion_multiplier': self.get_congestion_multiplier(),
            'transit_multiplier': self.get_transit_time_multiplier(),
            'roadworks_multiplier': self.get_roadworks_multiplier()
        }
