from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

app = Flask(__name__)
CORS(app)

initiatives = []
color_order = []
current_turn_index = 0
connected_devices = {}
host_device_id = None

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
        "color": data['color'],
        "isNPC": data.get('isNPC', False)
    }
    initiatives.append(new_initiative)
    initiatives.sort(key=lambda x: x['initiative'], reverse=True)
    return jsonify(new_initiative), 201

@app.route('/api/npcs', methods=['POST'])
def add_npc():
    data = request.json
    if not data or 'name' not in data or 'initiative' not in data:
        return jsonify({"error": "Invalid data"}), 400
    
    if host_device_id is None or host_device_id not in connected_devices:
        return jsonify({"error": "Host device not found"}), 400
    
    host_color = connected_devices[host_device_id]["color"]
    
    new_npc = {
        "id": str(uuid.uuid4()),
        "name": data['name'],
        "initiative": int(data['initiative']),
        "color": host_color,
        "isNPC": True
    }
    initiatives.append(new_npc)
    initiatives.sort(key=lambda x: x['initiative'], reverse=True)
    return jsonify(new_npc), 201

@app.route('/api/initiatives/<string:initiative_id>', methods=['DELETE'])
def delete_initiative(initiative_id):
    global initiatives
    initiatives = [init for init in initiatives if init['id'] != initiative_id]
    return '', 204

@app.route('/api/devices', methods=['GET'])
def get_connected_devices():
    return jsonify(connected_devices)

@app.route('/api/current-turn', methods=['GET', 'POST'])
def current_turn():
    global current_turn_index
    if request.method == 'POST':
        data = request.json
        if 'id' in data:
            try:
                current_turn_index = next(i for i, init in enumerate(initiatives) if init['id'] == data['id'])
                current_turn_index = (current_turn_index + 1) % len(initiatives)
            except StopIteration:
                return jsonify({"error": "Invalid initiative ID"}), 400
            return jsonify({"message": "Turn updated"}), 200
        return jsonify({"error": "Invalid data"}), 400
    else:
        if initiatives:
            current_initiative = initiatives[current_turn_index]
            return jsonify({
                "id": current_initiative['id'],
                "color": current_initiative['color'],
                "name": current_initiative['name']
            })
        return jsonify({"error": "No initiatives"}), 404

@app.route('/api/color-order', methods=['GET'])
def get_color_order():
    return jsonify(color_order)

if __name__ == '__main__':
    app.run('0.0.0.0',5000, debug=True)