#!/usr/bin/env python3
"""
Weather Effects Demonstration
Shows how different weather conditions affect the simulation
"""

from weather import WeatherSystem

print("=" * 70)
print("WEATHER SYSTEM EFFECTS DEMONSTRATION")
print("=" * 70)

weather_types = ['clear', 'rain', 'snow', 'heatwave']
icons = {'clear': '☀️', 'rain': '🌧️', 'snow': '❄️', 'heatwave': '🔥'}

for weather_type in weather_types:
    icon = icons[weather_type]
    print(f"\n{'=' * 70}")
    print(f"Weather: {weather_type.upper()} {icon}")
    print("=" * 70)
    
    # Create weather system and force specific weather
    weather = WeatherSystem("Demo City")
    weather.current_weather = weather_type
    
    # Get effects
    info = weather.get_weather_info()
    
    print(f"\n📊 MULTIPLIERS:")
    print(f"  Congestion Threshold: {weather.get_congestion_multiplier():.1f}x")
    print(f"  Transit Time:         {weather.get_transit_time_multiplier():.1f}x")
    print(f"  Roadworks Activity:   {weather.get_roadworks_multiplier():.1f}x")
    
    print(f"\n⚡ EFFECTS:")
    for effect in info['effects']:
        print(f"  • {effect}")
    
    print(f"\n🚗 EXAMPLE SCENARIOS:")
    
    # Congestion example
    base_threshold = 5
    adjusted = int(base_threshold * weather.get_congestion_multiplier())
    print(f"  Congestion: Traffic jams when {adjusted} vehicles on road")
    print(f"              (normally {base_threshold} vehicles)")
    
    # Transit time example
    base_time = 20  # minutes
    adjusted_time = int(base_time * weather.get_transit_time_multiplier())
    print(f"  Travel Time: {base_time} min trip becomes {adjusted_time} min")
    
    # Roadworks example
    if weather_type == 'heatwave':
        print(f"  Roadworks: 2x more construction zones appearing")
    elif weather_type == 'rain':
        print(f"  Roadworks: Construction stops, zones may be removed")
    else:
        print(f"  Roadworks: Normal construction activity")

print(f"\n{'=' * 70}")
print("WEATHER TRANSITION PROBABILITIES BY TIME OF DAY")
print("=" * 70)

time_periods = [
    ("Morning (6-10 AM)", {'clear': 0.4, 'rain': 0.3, 'snow': 0.2, 'heatwave': 0.1}),
    ("Midday (10 AM-2 PM)", {'clear': 0.3, 'rain': 0.2, 'snow': 0.1, 'heatwave': 0.4}),
    ("Afternoon (2-6 PM)", {'clear': 0.35, 'rain': 0.35, 'snow': 0.15, 'heatwave': 0.15}),
    ("Evening (6+ PM)", {'clear': 0.5, 'rain': 0.25, 'snow': 0.2, 'heatwave': 0.05})
]

for period, probs in time_periods:
    print(f"\n{period}:")
    for weather_type, prob in probs.items():
        icon = icons[weather_type]
        bar = '█' * int(prob * 20)
        print(f"  {icon} {weather_type.capitalize():10s} {bar:20s} {prob*100:5.1f}%")

print(f"\n{'=' * 70}")
print("KEY INSIGHTS")
print("=" * 70)
print("""
1. RAIN increases congestion dramatically
   - Roads that normally handle 5 cars now jam at 3 cars
   - Travel times increase by 30%
   - Great for testing congestion management

2. SNOW has the most severe impact on travel
   - Transit times DOUBLE (20 min → 40 min)
   - Severe delays during rush hour
   - Tests system resilience under extreme conditions

3. HEATWAVES create infrastructure challenges
   - Roadworks double, blocking more routes
   - Forces dynamic rerouting
   - Tests pathfinding adaptability

4. Each city has INDEPENDENT weather
   - City A can have rain while City B has sun
   - Enables comparison of weather impacts
   - More realistic multi-city scenarios

5. Weather changes DYNAMICALLY
   - Transitions every 1-4 hours
   - Time-based probabilities create realistic patterns
   - Keeps simulation interesting and varied
""")

print("=" * 70)
print("✅ Weather system ready for simulation!")
print("=" * 70)
