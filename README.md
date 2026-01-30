# Multi-City Traffic Simulation with Dynamic Weather

A sophisticated multi-city traffic simulation system that models realistic urban traffic patterns with dynamic weather conditions affecting traffic flow, congestion, and roadworks.

## Features

### Core Simulation
- **Multi-city support**: Simulate up to 5 cities simultaneously
- **Realistic traffic patterns**: Morning and evening commutes, social visits, shopping trips, and airport travel
- **Dynamic routing**: Pathfinding that avoids roadworks and considers congestion
- **Multiple location types**: Homes, apartments, workplaces, shops, subway stations, and airports
- **Real-time visualization**: Interactive D3.js-based network visualization

### Weather System (NEW!)
Each city has its own independent weather system that changes dynamically throughout the day:

#### Weather Types
1. **Clear** ☀️
   - Normal traffic conditions
   - Standard transit times
   - Regular roadwork activity

2. **Rain** 🌧️
   - **Increased congestion**: Traffic jams occur at lower vehicle counts (40% reduction in congestion threshold)
   - **Slower travel**: 30% increase in transit times
   - **Reduced roadworks**: Construction activity decreases

3. **Snow** ❄️
   - **Severe congestion**: Traffic jams occur much more easily (30% reduction in congestion threshold)
   - **Doubled transit times**: All travel takes twice as long
   - **Moderate congestion impact**: Similar to rain conditions

4. **Heatwave** 🔥
   - **Increased roadworks**: Road maintenance and construction doubles
   - **Normal traffic flow**: Standard congestion and transit times
   - **More construction zones**: New roadworks appear more frequently

#### Weather Dynamics
- Weather changes every 1-4 hours based on time of day
- Different weather types are more likely at different times:
  - **Morning (6-10 AM)**: Balanced mix of all weather types
  - **Midday (10 AM-2 PM)**: Higher chance of heatwaves
  - **Afternoon (2-6 PM)**: Increased rain probability
  - **Evening (6+ PM)**: More likely to be clear
- Each city has independent weather conditions
- Weather effects are displayed in real-time in the UI

## How to Run

### Prerequisites
```bash
pip install -r requirements.txt
```

### Start the Simulation
```bash
python app.py
```

Then open your browser to `http://localhost:5000`

### Configuration
1. Set the number of cities (1-5)
2. For each city, configure:
   - City name
   - Number of homes (10-100)
   - Number of workplaces (5-50)
   - Number of subway stations (0-30)
   - Optional: Upload a city map image for custom road layouts
3. Click "Start All Simulations"

## Weather Impact Examples

### Rain Scenario
- A road that normally handles 5 vehicles before congestion now jams at 3 vehicles
- A 10-minute commute becomes 13 minutes
- Roadwork zones may be removed as construction stops

### Snow Scenario
- Transit times double: a 15-minute trip takes 30 minutes
- Severe congestion occurs more easily
- Commuters experience significant delays

### Heatwave Scenario
- New roadwork zones appear frequently
- Roads may become blocked due to maintenance
- Traffic must reroute around construction zones
- Normal travel speeds maintained

## Technical Details

### Files
- `app.py`: Flask server and WebSocket handlers
- `city.py`: City graph structure and pathfinding
- `person.py`: Individual agent behavior and movement
- `simulation.py`: Simulation engine and tick logic
- `weather.py`: **NEW** - Weather system with dynamic conditions
- `templates/index.html`: Web interface with weather display

### Weather System Architecture
The `WeatherSystem` class manages:
- Weather state transitions
- Time-based weather probabilities
- Effect multipliers for congestion, transit time, and roadworks
- Weather history tracking

Weather effects are applied at multiple levels:
- **City level**: Roadwork generation/removal
- **Person level**: Congestion threshold adjustments
- **Path level**: Transit time calculations

## Simulation Time
- Runs from 7:00 AM to 7:00 PM (simulation time)
- Each tick represents 5 minutes
- Weather updates occur every tick
- Weather changes every 60-240 minutes

## Visualization
- **Nodes**: Color-coded by type (homes, work, shops, apartments, airport)
- **Edges**: Color and thickness indicate traffic levels
- **Roadworks**: Shown as dashed brown lines
- **Weather Panel**: Real-time weather display with effects
- **Road Statistics**: Current and peak traffic for each road

Enjoy exploring how weather conditions affect urban traffic patterns!