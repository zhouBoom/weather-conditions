from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import random
import base64
import io
from PIL import Image
import numpy as np
import cv2

from city import City
from person import Person
from simulation import WebSimulation

app = Flask(__name__)
app.config['SECRET_KEY'] = 'simulation_key'
socketio = SocketIO(app, cors_allowed_origins="*")

active_simulations = {}  # Dictionary to store multiple simulations by city_id
simulation_counter = 0

def process_city_map_image(image_data):
    """
    Process uploaded city map image to extract road network layout.
    Returns grid positions for nodes based on road intersections.
    """
    try:
        # Validate image data format
        if not image_data or ',' not in image_data:
            raise ValueError("Invalid image data format")
        
        # Decode base64 image
        header, encoded = image_data.split(',', 1)
        
        # Validate that it's an image
        if 'image' not in header.lower():
            raise ValueError("File is not an image")
        
        image_bytes = base64.b64decode(encoded)
        
        # Validate image size (limit to 5MB)
        if len(image_bytes) > 5 * 1024 * 1024:
            raise ValueError("Image file too large (max 5MB)")
        
        # Open image with PIL
        try:
            pil_image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValueError(f"Cannot open image file: {str(e)}")
        
        # Validate image dimensions
        width, height = pil_image.size
        if width > 2000 or height > 2000:
            raise ValueError("Image dimensions too large (max 2000x2000)")
        
        if width < 100 or height < 100:
            raise ValueError("Image dimensions too small (min 100x100)")
        
        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Convert to numpy array for OpenCV processing
        img_array = np.array(pil_image)
        
        # Convert RGB to BGR for OpenCV
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply edge detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Apply morphological operations to connect broken lines
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # Find contours (potential roads)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create a mask for roads
        road_mask = np.zeros_like(gray)
        cv2.drawContours(road_mask, contours, -1, 255, 2)
        
        # Find intersection points using corner detection
        corners = cv2.goodFeaturesToTrack(road_mask, maxCorners=200, qualityLevel=0.01, minDistance=20)
        
        if corners is None or len(corners) < 10:
            raise ValueError("Could not detect enough road intersections in image")
        
        # Convert corner coordinates to grid positions
        height, width = gray.shape
        grid_positions = {}
        
        # Normalize coordinates to a reasonable grid size
        max_grid_size = 20
        
        for i, corner in enumerate(corners):
            x, y = corner.ravel()
            
            # Convert pixel coordinates to grid coordinates
            grid_x = int((x / width) * max_grid_size)
            grid_y = int((y / height) * max_grid_size)
            
            # Ensure coordinates are within bounds
            grid_x = max(0, min(grid_x, max_grid_size - 1))
            grid_y = max(0, min(grid_y, max_grid_size - 1))
            
            # Use a unique identifier for each position
            position_key = f"IMG_{i}"
            grid_positions[position_key] = (grid_y, grid_x)
        
        print(f"[DEBUG] Successfully processed image: extracted {len(grid_positions)} positions")
        return grid_positions
        
    except ValueError as e:
        print(f"[ERROR] Image processing validation error: {e}")
        raise e
    except Exception as e:
        print(f"[ERROR] Failed to process image: {e}")
        raise ValueError(f"Image processing failed: {str(e)}")

def generate_people(city):
    people = []
    
    # Generate people for regular homes (1 person each)
    for home in city.home_nodes:
        if random.random() < 0.2:
            p = Person(home, None, city)
        else:
            work = random.choice(city.work_nodes)
            p = Person(home, work, city)
        people.append(p)
    
    # Generate people for apartments (10 people each)
    for apartment in city.apartment_nodes:
        for i in range(10):
            if random.random() < 0.2:
                p = Person(apartment, None, city)
            else:
                work = random.choice(city.work_nodes)
                p = Person(apartment, work, city)
            people.append(p)
    
    return people

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_simulation')
def handle_start_simulation(data):
    global active_simulations, simulation_counter

    print("[DEBUG] Received 'start_simulation' event with data keys:", list(data.keys()))

    try:
        num_cities = int(data.get('numCities', 1))
        cities_config = data.get('citiesConfig', [])
        
        if not (1 <= num_cities <= 5):
            emit('error', {'message': 'Number of cities must be between 1 and 5.'})
            return
            
        if len(cities_config) != num_cities:
            emit('error', {'message': 'Cities configuration mismatch.'})
            return
            
        print(f"[DEBUG] Creating {num_cities} cities")
    except (TypeError, ValueError) as e:
        print(f"[ERROR] Invalid input types: {e}")
        emit('error', {'message': 'Invalid input data.'})
        return

    # Stop all existing simulations
    for sim_id, sim in active_simulations.items():
        sim.running = False
    active_simulations.clear()

    created_cities = []
    
    for i, city_config in enumerate(cities_config):
        try:
            homes = int(city_config.get('homes', 40))
            works = int(city_config.get('works', 20))
            subways = int(city_config.get('subways', 5))
            map_image = city_config.get('mapImage')
            city_name = city_config.get('name', f'City {i+1}')
            
            if not (10 <= homes <= 100 and 5 <= works <= 50 and 0 <= subways <= 30):
                emit('error', {'message': f'Invalid sizes for {city_name}: homes 10–100, works 5–50, subways 0-30.'})
                return
                
            print(f"[DEBUG] Creating {city_name} with homes={homes}, works={works}, subways={subways}")
            
            # Process uploaded image if provided
            image_grid_positions = None
            if map_image:
                print(f"[DEBUG] Processing uploaded city map image for {city_name}")
                try:
                    image_grid_positions = process_city_map_image(map_image)
                    if image_grid_positions:
                        print(f"[DEBUG] Extracted {len(image_grid_positions)} positions from image for {city_name}")
                    else:
                        print(f"[WARNING] No positions extracted from image for {city_name}, falling back to default layout")
                except ValueError as e:
                    print(f"[ERROR] Image processing error for {city_name}: {e}")
                    emit('error', {'message': f'Image processing error for {city_name}: {str(e)}'})
                    return
                except Exception as e:
                    print(f"[ERROR] Unexpected image processing error for {city_name}: {e}")
                    emit('error', {'message': f'Failed to process image for {city_name}. Please try a different image.'})
                    return

            city = City(home_count=homes, work_count=works, subway_count=subways, 
                       image_positions=image_grid_positions)
            people = generate_people(city)

            simulation_counter += 1
            city_id = f"city_{simulation_counter}"
            
            simulation = WebSimulation(city, people, socketio, city_id, city_name)
            active_simulations[city_id] = simulation
            
            created_cities.append({
                'id': city_id,
                'name': city_name,
                'homes': homes,
                'works': works,
                'subways': subways,
                'people': len(people),
                'used_image': image_grid_positions is not None
            })

            print(f"[DEBUG] Created {city_name} with {len(city.home_nodes)} homes, {len(city.work_nodes)} works")
            
        except Exception as e:
            print(f"[ERROR] Failed to create city {i+1}: {e}")
            emit('error', {'message': f'Failed to create city {i+1}: {str(e)}'})
            return

    # Start all simulations
    for city_id, simulation in active_simulations.items():
        print(f"[DEBUG] Starting simulation thread for {simulation.city_name}")
        socketio.start_background_task(simulation.run)

    emit('simulations_started', {
        'cities': created_cities
    })
    print("[DEBUG] Emitted 'simulations_started' event")

@socketio.on('stop_simulation')
def handle_stop_simulation(data=None):
    global active_simulations
    
    city_id = data.get('cityId') if data else None
    
    if city_id and city_id in active_simulations:
        # Stop specific city
        active_simulations[city_id].running = False
        del active_simulations[city_id]
        emit('city_simulation_stopped', {'cityId': city_id})
    else:
        # Stop all simulations
        for sim in active_simulations.values():
            sim.running = False
        active_simulations.clear()
        emit('all_simulations_stopped')

@socketio.on('get_city_data')
def handle_get_city_data(data):
    city_id = data.get('cityId')
    if city_id in active_simulations:
        simulation = active_simulations[city_id]
        city_data = simulation.get_simulation_data()
        emit('city_data_update', {
            'cityId': city_id,
            'data': city_data
        })

@socketio.on('get_active_cities')
def handle_get_active_cities():
    cities = []
    for city_id, simulation in active_simulations.items():
        cities.append({
            'id': city_id,
            'name': simulation.city_name,
            'running': simulation.running
        })
    emit('active_cities_list', {'cities': cities})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)