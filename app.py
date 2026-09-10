import os
import csv
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
DATA_FILE = os.path.join(DATA_DIR, 'energy_data.csv')
SAMPLE_DATA_FILE = os.path.join(DATA_DIR, 'sample_data.json')

# Key Constants
CO2_FACTOR = 0.82  # kg of CO2 saved per kWh of renewable energy
DEFAULT_TARIFF = 8.0  # ₹ per kWh

# Load Definitions with Priority Levels
loads_state = [
    {
        'id': 'load_high',
        'name': 'Essential Emergency & Security Load',
        'category': 'High Priority',
        'priority': 1,
        'power_w': 120,
        'status': 'ON',
        'mode': 'AUTO',
        'description': 'Critical medical, security sensors & LED emergency lighting.'
    },
    {
        'id': 'load_med',
        'name': 'Ventilation & Cooling Fan Load',
        'category': 'Medium Priority',
        'priority': 2,
        'power_w': 300,
        'status': 'ON',
        'mode': 'AUTO',
        'description': 'Controllable air circulator, refrigeration & work fans.'
    },
    {
        'id': 'load_low',
        'name': 'EV Charger / Thermal Heating Load',
        'category': 'Low Priority',
        'priority': 3,
        'power_w': 600,
        'status': 'OFF',
        'mode': 'AUTO',
        'description': 'Non-essential heavy appliances, water pump & EV charging station.'
    }
]

# System Telemetry Cache
latest_telemetry = {
    'voltage': 14.2,
    'current': 2.1,
    'power': 29.82,
    'solar_generated': 29.82,
    'energy_consumed': 14.20,
    'battery_pct': 82.0,
    'electricity_price': DEFAULT_TARIFF,
    'solar_used': 14.20,
    'grid_energy': 0.0,
    'excess_energy': 15.62,
    'money_saved': 113.60,
    'co2_reduction': 11.64,
    'renewable_utilization': 100.0,
    'energy_saved_kWh': 4.80,
    'source': 'simulation',
    'active_scenario': 'Normal Generation',
    'last_seen': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

def ensure_data_files():
    """Ensure data directory, CSV file, and sample JSON file exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'voltage', 'current', 'power', 'solar_generated',
                'energy_consumed', 'battery_pct', 'electricity_price', 'solar_used',
                'grid_energy', 'excess_energy', 'money_saved', 'co2_reduction',
                'renewable_utilization', 'active_loads', 'source'
            ])

    if not os.path.exists(SAMPLE_DATA_FILE):
        sample_records = [
            {"timestamp": "2026-09-10 08:00:00", "voltage": 11.5, "current": 0.8, "power": 9.2, "solar_generated": 9.2, "energy_consumed": 7.0, "battery_pct": 65.0, "source": "sample"},
            {"timestamp": "2026-09-10 10:00:00", "voltage": 14.0, "current": 2.0, "power": 28.0, "solar_generated": 28.0, "energy_consumed": 12.0, "battery_pct": 78.0, "source": "sample"},
            {"timestamp": "2026-09-10 12:00:00", "voltage": 18.5, "current": 3.2, "power": 59.2, "solar_generated": 59.2, "energy_consumed": 22.0, "battery_pct": 95.0, "source": "sample"},
            {"timestamp": "2026-09-10 14:00:00", "voltage": 16.2, "current": 2.5, "power": 40.5, "solar_generated": 40.5, "energy_consumed": 18.5, "battery_pct": 88.0, "source": "sample"},
            {"timestamp": "2026-09-10 16:00:00", "voltage": 12.8, "current": 1.1, "power": 14.08, "solar_generated": 14.08, "energy_consumed": 10.2, "battery_pct": 72.0, "source": "sample"}
        ]
        with open(SAMPLE_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(sample_records, f, indent=2)

def execute_smart_load_management(solar_power, battery_pct):
    """
    Priority Load Control Algorithm:
    - High Priority (Essential): ON unless battery <= 5%
    - Medium Priority (Controllable): ON if (solar >= 15W OR battery >= 30%)
    - Low Priority (Non-Essential): ON only if (solar >= 30W AND battery >= 60%) OR battery >= 85%
    """
    switched_off_count = 0
    switched_on_count = 0
    total_saved_w = 0

    for load in loads_state:
        if load['mode'] != 'AUTO':
            continue

        previous_status = load['status']
        new_status = 'OFF'

        if load['id'] == 'load_high':
            # Essential Load
            new_status = 'ON' if battery_pct > 5.0 else 'OFF'
        elif load['id'] == 'load_med':
            # Medium Priority Load
            if solar_power >= 15.0 or battery_pct >= 30.0:
                new_status = 'ON'
            else:
                new_status = 'OFF'
        elif load['id'] == 'load_low':
            # Low Priority Load
            if (solar_power >= 30.0 and battery_pct >= 60.0) or battery_pct >= 85.0:
                new_status = 'ON'
            else:
                new_status = 'OFF'

        load['status'] = new_status

        if previous_status != new_status:
            if new_status == 'OFF':
                switched_off_count += 1
            else:
                switched_on_count += 1

        if load['status'] == 'OFF':
            total_saved_w += load['power_w']

    active_loads_count = sum(1 for l in loads_state if l['status'] == 'ON')
    return active_loads_count, switched_on_count, switched_off_count, total_saved_w

def generate_smart_recommendations(solar_gen, consumed, battery, excess, voltage=None, current=None):
    """Generate real-time advisory alerts based on current system conditions."""
    recommendations = []

    if solar_gen >= 30.0 or (voltage and voltage >= 16.0):
        recommendations.append({
            'type': 'success',
            'title': 'High Solar Generation Peak ☀️',
            'message': 'Abundant solar power available! Low-priority loads (EV charging & heating) auto-enabled.'
        })
    elif solar_gen < 10.0 or (voltage and voltage < 10.0):
        recommendations.append({
            'type': 'warning',
            'title': 'Low Solar Output Detected ☁️',
            'message': 'Solar irradiance is minimal. Low-priority loads shed automatically to conserve energy.'
        })

    if battery < 25.0:
        recommendations.append({
            'type': 'danger',
            'title': 'Critical Battery Level Alert 🪫',
            'message': 'Battery level below 25%. System preserved for High Priority Essential Load only.'
        })
    elif battery >= 80.0:
        recommendations.append({
            'type': 'info',
            'title': 'Battery Storage Fully Charged 🔋',
            'message': 'Battery reserve above 80%. Maximum microgrid reliability active.'
        })

    if excess > 0.0:
        recommendations.append({
            'type': 'success',
            'title': 'Surplus Renewable Energy 📦',
            'message': f'Surplus clean energy of {excess:.2f} kWh routed to storage.'
        })
    elif consumed > solar_gen:
        deficit = consumed - solar_gen
        recommendations.append({
            'type': 'warning',
            'title': 'Grid / Storage Assistance Active 🔌',
            'message': f'Load demand exceeds solar output by {deficit:.2f} kWh. Supported via battery storage.'
        })

    return recommendations

def read_csv_data():
    """Read stored historical logs from CSV."""
    ensure_data_files()
    records = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append({
                    'date': row.get('timestamp', ''),
                    'voltage': float(row.get('voltage', 0.0)),
                    'current': float(row.get('current', 0.0)),
                    'power': float(row.get('power', 0.0)),
                    'solar_generated': float(row.get('solar_generated', 0.0)),
                    'energy_consumed': float(row.get('energy_consumed', 0.0)),
                    'battery_pct': float(row.get('battery_pct', 0.0)),
                    'electricity_price': float(row.get('electricity_price', DEFAULT_TARIFF)),
                    'solar_used': float(row.get('solar_used', 0.0)),
                    'grid_energy': float(row.get('grid_energy', 0.0)),
                    'excess_energy': float(row.get('excess_energy', 0.0)),
                    'money_saved': float(row.get('money_saved', 0.0)),
                    'co2_reduction': float(row.get('co2_reduction', 0.0)),
                    'renewable_utilization': float(row.get('renewable_utilization', 100.0)),
                    'active_loads': row.get('active_loads', '2/3'),
                    'source': row.get('source', 'unknown')
                })
    return records

# -----------------------------------------------------------------------------
# Web Page Routes
# -----------------------------------------------------------------------------
@app.route('/')
@app.route('/dashboard')
def index():
    """Render main EcoPower Web Dashboard."""
    return render_template('index.html')

@app.route('/about')
def about():
    """Render About Project & SIH 2026 page."""
    return render_template('about.html')

@app.route('/hardware')
def hardware_page():
    """Render Hardware Specifications & Wiring Guide page."""
    return render_template('hardware.html')

# -----------------------------------------------------------------------------
# REST API Endpoints
# -----------------------------------------------------------------------------
@app.route('/api/status', methods=['GET'])
def get_status():
    """Return high-level system status and connectivity."""
    is_hardware = latest_telemetry.get('source') == 'esp32_hardware'
    active_loads = sum(1 for l in loads_state if l['status'] == 'ON')
    
    return jsonify({
        'success': True,
        'system_status': 'OPTIMAL' if latest_telemetry['battery_pct'] > 20 else 'WARNING',
        'hardware_connected': is_hardware,
        'connection_mode': 'ESP32 Hardware Node' if is_hardware else 'Software Simulation Mode',
        'active_scenario': latest_telemetry.get('active_scenario', 'Live Run'),
        'active_loads_count': active_loads,
        'total_loads_count': len(loads_state),
        'latest_telemetry': latest_telemetry
    })

@app.route('/api/energy', methods=['GET', 'POST'])
@app.route('/analyze', methods=['POST'])
def process_energy_data():
    """
    Handle GET (solar telemetry summary) and POST (ingest telemetry or run analysis).
    """
    global latest_telemetry

    if request.method == 'GET':
        return jsonify({
            'success': True,
            'solar_generated': latest_telemetry['solar_generated'],
            'energy_consumed': latest_telemetry['energy_consumed'],
            'solar_used': latest_telemetry['solar_used'],
            'excess_energy': latest_telemetry['excess_energy'],
            'grid_energy': latest_telemetry['grid_energy'],
            'renewable_utilization': latest_telemetry['renewable_utilization'],
            'voltage': latest_telemetry['voltage'],
            'current': latest_telemetry['current'],
            'power': latest_telemetry['power'],
            'money_saved': latest_telemetry['money_saved'],
            'co2_reduction': latest_telemetry['co2_reduction']
        })

    try:
        data = request.get_json(force=True) if request.is_json else request.form.to_dict()
        source = data.get('source', 'esp32_hardware' if request.is_json else 'manual')

        voltage = float(data.get('voltage', 12.0))
        current = float(data.get('current', 1.0))
        power = float(data.get('power', round(voltage * current, 2)))
        battery_pct = float(data.get('battery_pct', data.get('battery', 75.0)))
        electricity_price = float(data.get('electricity_price', DEFAULT_TARIFF))

        # Input Validation
        if voltage < 0 or current < 0 or power < 0 or electricity_price < 0:
            return jsonify({'error': 'Voltage, current, power, and tariff cannot be negative.'}), 400
        if not (0 <= battery_pct <= 100):
            return jsonify({'error': 'Battery percentage must be between 0% and 100%.'}), 400

        # Execute Smart Load Management Algorithm
        active_loads, switched_on, switched_off, saved_w = execute_smart_load_management(power, battery_pct)

        # Dynamic Load Consumption calculation based on active loads (kW/kWh active window)
        base_active_power_w = sum(l['power_w'] for l in loads_state if l['status'] == 'ON')
        if 'energy_consumed' in data:
            energy_consumed = float(data.get('energy_consumed'))
        elif 'load' in data:
            energy_consumed = float(data.get('load'))
        else:
            energy_consumed = round(base_active_power_w / 100.0, 2)

        solar_generated = float(data.get('solar_generated', power))

        # Core Renewable Energy Metrics
        solar_used = round(min(solar_generated, energy_consumed), 2)
        excess_energy = round(max(0.0, solar_generated - energy_consumed), 2)
        grid_energy = round(max(0.0, energy_consumed - solar_generated), 2)
        money_saved = round(solar_used * electricity_price, 2)
        co2_reduction = round(solar_used * CO2_FACTOR, 2)

        # Renewable Utilization Percentage
        if energy_consumed > 0:
            renewable_utilization = round(min(100.0, (solar_used / energy_consumed) * 100.0), 1)
        else:
            renewable_utilization = 100.0

        energy_saved_kWh = round(saved_w / 100.0, 2)

        recommendations = generate_smart_recommendations(
            solar_generated, energy_consumed, battery_pct, excess_energy, voltage, current
        )

        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Cache Update
        latest_telemetry = {
            'voltage': round(voltage, 2),
            'current': round(current, 2),
            'power': round(power, 2),
            'solar_generated': round(solar_generated, 2),
            'energy_consumed': round(energy_consumed, 2),
            'battery_pct': round(battery_pct, 1),
            'electricity_price': round(electricity_price, 2),
            'solar_used': solar_used,
            'grid_energy': grid_energy,
            'excess_energy': excess_energy,
            'money_saved': money_saved,
            'co2_reduction': co2_reduction,
            'renewable_utilization': renewable_utilization,
            'energy_saved_kWh': energy_saved_kWh,
            'active_loads_count': active_loads,
            'switched_on_count': switched_on,
            'switched_off_count': switched_off,
            'source': source,
            'active_scenario': data.get('scenario', latest_telemetry.get('active_scenario', 'Custom Run')),
            'last_seen': current_timestamp
        }

        # CSV Logging
        ensure_data_files()
        with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                current_timestamp, round(voltage, 2), round(current, 2), round(power, 2),
                solar_generated, energy_consumed, battery_pct, electricity_price,
                solar_used, grid_energy, excess_energy, money_saved, co2_reduction,
                renewable_utilization, f"{active_loads}/{len(loads_state)}", source
            ])

        return jsonify({
            'success': True,
            'data': latest_telemetry,
            'loads': loads_state,
            'recommendations': recommendations
        })

    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid numeric input format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Server error processing energy telemetry: {str(e)}'}), 500

@app.route('/api/battery', methods=['GET'])
def get_battery_status():
    """Return detailed battery metrics and health state."""
    pct = latest_telemetry['battery_pct']
    if pct > 80:
        state = 'FULL'
        health = 'EXCELLENT'
    elif pct > 30:
        state = 'NORMAL'
        health = 'GOOD'
    elif pct > 15:
        state = 'LOW'
        health = 'FAIR'
    else:
        state = 'CRITICAL'
        health = 'WARNING'

    return jsonify({
        'success': True,
        'battery_pct': pct,
        'battery_voltage': round(11.0 + (pct / 100.0) * 2.8, 2), # Estimated 12V LiFePO4 battery curve
        'state': state,
        'health': health,
        'backup_hours_est': round((pct / 100.0) * 6.5, 1)
    })

@app.route('/api/loads', methods=['GET'])
def get_loads():
    """Return priority load status and smart controller state."""
    active_count = sum(1 for l in loads_state if l['status'] == 'ON')
    total_power_w = sum(l['power_w'] for l in loads_state if l['status'] == 'ON')
    
    return jsonify({
        'success': True,
        'loads': loads_state,
        'active_count': active_count,
        'total_count': len(loads_state),
        'active_power_w': total_power_w
    })

@app.route('/api/load-control', methods=['POST'])
def control_load():
    """
    Toggle load status (ON/OFF) or set load control mode (AUTO/MANUAL).
    """
    try:
        data = request.get_json(force=True)
        load_id = data.get('load_id')
        action = data.get('action') # 'toggle', 'ON', 'OFF', 'set_mode_auto', 'set_mode_manual'

        target_load = next((l for l in loads_state if l['id'] == load_id), None)
        if not target_load:
            return jsonify({'error': f'Load with ID "{load_id}" not found.'}), 404

        if action == 'toggle':
            target_load['status'] = 'OFF' if target_load['status'] == 'ON' else 'ON'
            target_load['mode'] = 'MANUAL'
        elif action in ['ON', 'OFF']:
            target_load['status'] = action
            target_load['mode'] = 'MANUAL'
        elif action == 'set_mode_auto':
            target_load['mode'] = 'AUTO'
            # Re-run smart algorithm
            execute_smart_load_management(latest_telemetry['power'], latest_telemetry['battery_pct'])
        elif action == 'set_mode_manual':
            target_load['mode'] = 'MANUAL'
        else:
            return jsonify({'error': f'Unsupported load action: {action}'}), 400

        active_count = sum(1 for l in loads_state if l['status'] == 'ON')
        latest_telemetry['active_loads_count'] = active_count

        return jsonify({
            'success': True,
            'message': f"Load '{target_load['name']}' updated to {target_load['status']} ({target_load['mode']}).",
            'load': target_load,
            'loads': loads_state
        })

    except Exception as e:
        return jsonify({'error': f'Failed to execute load control: {str(e)}'}), 500

@app.route('/api/simulation', methods=['POST'])
def run_simulation():
    """
    Apply Hackathon Preset Simulation Scenarios.
    Presets:
    - 'high_solar': Abundant sun, 22V, 2.5A, 90% battery.
    - 'normal': Moderate sun, 13.5V, 1.2A, 70% battery.
    - 'low_solar': Cloud cover, 8V, 0.4A, 55% battery.
    - 'low_battery': Critical battery, 5V, 0.1A, 18% battery.
    - 'high_demand': High energy consumption requirement.
    - 'energy_saving': Eco mode with optimized load shedding.
    """
    global latest_telemetry
    try:
        data = request.get_json(force=True) if request.is_json else request.form.to_dict()
        scenario = data.get('scenario', 'normal').lower()

        preset_configs = {
            'high_solar': {
                'voltage': 22.0, 'current': 2.5, 'power': 55.0,
                'solar_generated': 55.0, 'energy_consumed': 18.0, 'battery_pct': 92.0,
                'active_scenario': 'High Solar Generation ☀️'
            },
            'normal': {
                'voltage': 13.5, 'current': 1.2, 'power': 16.2,
                'solar_generated': 16.2, 'energy_consumed': 10.5, 'battery_pct': 75.0,
                'active_scenario': 'Normal Generation 🌤️'
            },
            'low_solar': {
                'voltage': 8.0, 'current': 0.4, 'power': 3.2,
                'solar_generated': 3.2, 'energy_consumed': 6.0, 'battery_pct': 52.0,
                'active_scenario': 'Low Solar Generation ☁️'
            },
            'low_battery': {
                'voltage': 5.0, 'current': 0.1, 'power': 0.5,
                'solar_generated': 0.5, 'energy_consumed': 2.5, 'battery_pct': 18.0,
                'active_scenario': 'Low Battery Emergency 🪫'
            },
            'high_demand': {
                'voltage': 14.0, 'current': 1.8, 'power': 25.2,
                'solar_generated': 25.2, 'energy_consumed': 32.0, 'battery_pct': 60.0,
                'active_scenario': 'High Load Demand ⚡'
            },
            'energy_saving': {
                'voltage': 12.5, 'current': 1.0, 'power': 12.5,
                'solar_generated': 12.5, 'energy_consumed': 4.2, 'battery_pct': 85.0,
                'active_scenario': 'Energy Saving Eco Mode 🌿'
            }
        }

        config = preset_configs.get(scenario, preset_configs['normal'])

        # Allows custom parameter overrides within simulation payload
        voltage = float(data.get('voltage', config['voltage']))
        current = float(data.get('current', config['current']))
        power = float(data.get('power', config['power']))
        battery_pct = float(data.get('battery_pct', config['battery_pct']))
        energy_consumed = float(data.get('energy_consumed', config['energy_consumed']))
        solar_generated = float(data.get('solar_generated', config['solar_generated']))
        electricity_price = float(data.get('electricity_price', DEFAULT_TARIFF))

        # Reset load modes to AUTO for scenario test
        for l in loads_state:
            l['mode'] = 'AUTO'

        # Execute load controller
        active_loads, switched_on, switched_off, saved_w = execute_smart_load_management(power, battery_pct)

        solar_used = round(min(solar_generated, energy_consumed), 2)
        excess_energy = round(max(0.0, solar_generated - energy_consumed), 2)
        grid_energy = round(max(0.0, energy_consumed - solar_generated), 2)
        money_saved = round(solar_used * electricity_price, 2)
        co2_reduction = round(solar_used * CO2_FACTOR, 2)

        renewable_utilization = round(min(100.0, (solar_used / energy_consumed) * 100.0), 1) if energy_consumed > 0 else 100.0
        energy_saved_kWh = round(saved_w / 100.0, 2)

        recommendations = generate_smart_recommendations(
            solar_generated, energy_consumed, battery_pct, excess_energy, voltage, current
        )

        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        latest_telemetry = {
            'voltage': round(voltage, 2),
            'current': round(current, 2),
            'power': round(power, 2),
            'solar_generated': round(solar_generated, 2),
            'energy_consumed': round(energy_consumed, 2),
            'battery_pct': round(battery_pct, 1),
            'electricity_price': round(electricity_price, 2),
            'solar_used': solar_used,
            'grid_energy': grid_energy,
            'excess_energy': excess_energy,
            'money_saved': money_saved,
            'co2_reduction': co2_reduction,
            'renewable_utilization': renewable_utilization,
            'energy_saved_kWh': energy_saved_kWh,
            'active_loads_count': active_loads,
            'switched_on_count': switched_on,
            'switched_off_count': switched_off,
            'source': 'simulation',
            'active_scenario': config['active_scenario'],
            'last_seen': current_timestamp
        }

        ensure_data_files()
        with open(DATA_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                current_timestamp, round(voltage, 2), round(current, 2), round(power, 2),
                solar_generated, energy_consumed, battery_pct, electricity_price,
                solar_used, grid_energy, excess_energy, money_saved, co2_reduction,
                renewable_utilization, f"{active_loads}/{len(loads_state)}", 'simulation'
            ])

        return jsonify({
            'success': True,
            'scenario': scenario,
            'message': f"Activated simulation scenario: {config['active_scenario']}",
            'data': latest_telemetry,
            'loads': loads_state,
            'recommendations': recommendations
        })

    except Exception as e:
        return jsonify({'error': f'Failed to trigger simulation scenario: {str(e)}'}), 500

@app.route('/api/latest', methods=['GET'])
def get_latest_telemetry():
    """Return the current cached telemetry snapshot."""
    is_hardware = latest_telemetry.get('source') == 'esp32_hardware'
    return jsonify({
        'success': True,
        'hardware_connected': is_hardware,
        'telemetry': latest_telemetry,
        'loads': loads_state
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    """Return logged telemetry records and cumulative summary stats."""
    records = read_csv_data()
    
    total_solar = sum(r['solar_generated'] for r in records)
    total_consumed = sum(r['energy_consumed'] for r in records)
    total_savings = sum(r['money_saved'] for r in records)
    total_co2 = sum(r['co2_reduction'] for r in records)
    
    summary = {
        'total_solar': round(total_solar, 2),
        'total_consumed': round(total_consumed, 2),
        'total_savings': round(total_savings, 2),
        'total_co2': round(total_co2, 2),
        'record_count': len(records)
    }

    return jsonify({'history': records, 'summary': summary})

if __name__ == '__main__':
    ensure_data_files()
    print("\n========================================================")
    print(" EcoPower - Smart Renewable Solar Energy System (SIH 2026)")
    print(" Running Flask Backend on http://127.0.0.1:5000")
    print("========================================================\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
