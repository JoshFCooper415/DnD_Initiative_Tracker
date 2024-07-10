from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

app = Flask(__name__)
CORS(app)

initiatives = []
connected_devices = {}
host_device_id = None
current_turn_index = 0

DISTINCT_COLORS = [
    "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF",
    "#FFA500", "#800080", "#008000", "#FFC0CB", "#A52A2A", "#808080",
    "#000000", "#FFFFFF", "#FFD700", "#4B0082", "#7FFF00", "#FF4500",
    "#1E90FF", "#8B4513"
]

color_index = 0

def get_next_color():
    global color_index
    color = DISTINCT_COLORS[color_index % len(DISTINCT_COLORS)]
    color_index += 1
    return color

@app.route('/api/connect', methods=['GET'])
def connect_device():
    global host_device_id
    device_id = str(uuid.uuid4())
    color = get_next_color()
    is_host = host_device_id is None
    if is_host:
        host_device_id = device_id
    connected_devices[device_id] = {"color": color, "isHost": is_host}
    return jsonify({"device_id": device_id, "color": color, "isHost": is_host})

@app.route('/api/disconnect/<string:device_id>', methods=['POST'])
def disconnect_device(device_id):
    global host_device_id
    if device_id in connected_devices:
        del connected_devices[device_id]
        if device_id == host_device_id:
            host_device_id = next(iter(connected_devices)) if connected_devices else None
            if host_device_id:
                connected_devices[host_device_id]["isHost"] = True
        return jsonify({"message": "Device disconnected"}), 200
    return jsonify({"error": "Device not found"}), 404

@app.route('/api/initiatives', methods=['GET'])
def get_initiatives():
    return jsonify(initiatives)

@app.route('/api/initiatives', methods=['POST'])
def add_initiative():
    data = request.json
    if not data or 'name' not in data or 'initiative' not in data or 'color' not in data:
        return jsonify({"error": "Invalid data"}), 400
    
    new_initiative = {
        "id": str(uuid.uuid4()),
        "name": data['name'],
        "initiative": int(data['initiative']),
        "color": data['color']
    }
    initiatives.append(new_initiative)
    initiatives.sort(key=lambda x: x['initiative'], reverse=True)
    return jsonify(new_initiative), 201

@app.route('/api/initiatives/<string:initiative_id>', methods=['DELETE'])
def delete_initiative(initiative_id):
    global initiatives
    initiatives = [init for init in initiatives if init['id'] != initiative_id]
    return '', 204

@app.route('/api/devices', methods=['GET'])
def get_connected_devices():
    return jsonify(connected_devices)

@app.route('/api/next-turn', methods=['POST'])
def next_turn():
    global current_turn_index
    if not initiatives:
        return jsonify({"error": "No initiatives"}), 404
    
    current_turn_index = (current_turn_index + 1) % len(initiatives)
    current_initiative = initiatives[current_turn_index]
    
    return jsonify({
        "id": current_initiative['id'],
        "color": current_initiative['color'],
        "name": current_initiative['name']
    }), 200

@app.route('/api/current-turn', methods=['GET'])
def get_current_turn():
    if not initiatives:
        return jsonify({"error": "No initiatives"}), 404
    
    current_initiative = initiatives[current_turn_index]
    return jsonify({
        "id": current_initiative['id'],
        "color": current_initiative['color'],
        "name": current_initiative['name']
    })

if __name__ == '__main__':
    app.run('0.0.0.0',debug=True)