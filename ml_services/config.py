"""
CityPulse-X Configuration — All constants, rules, and tuning parameters.
"""

# ─── SYSTEM PARAMS ───
C_i = 25.0              # Capacity per lane (vehicles)
G_min = 10.0             # Minimum green time (seconds)
G_max_peak = 55.0        # Maximum green time cap (seconds)
BETA = 50.0              # Green extension sensitivity
ALPHA = 0.4              # Density weighting factor
R_min = 8.0              # Minimum red time (seconds)
FAIRNESS_TIMER = 90.0    # Max wait before forced switch

K_THRESHOLD = 3          # Consecutive EV detections before confirmed
MAX_HOURLY_VOL = 6000.0  # Max predicted hourly volume (for normalization)
CONF_LEVEL = 0.35        # YOLO confidence threshold
JITTER_THRESHOLD = 4.0   # Bbox jitter suppression threshold
SMOOTHING_FACTOR = 0.6   # EMA smoothing for bbox positions

# ─── LANE MAPPINGS ───
LANE_MAP = {"lane1": 0, "lane2": 1, "lane3": 2, "lane4": 3}
LANE_PREFIXES = {0: 'N', 1: 'E', 2: 'S', 3: 'W'}

# ─── EMERGENCY PRIORITY MATRIX (Rule E3) ───
EV_PRIORITY = {
    "Ambulance": 3,
    "Fire Engine": 2,
    "Police Vehicle": 1
}

# ─── TRAFFIC RULES ───
TRAFFIC_RULES = {
    "G1": {"name": "Off-Peak Low Density", "density_threshold": 0.25, "G_min": 10.0},
    "G2": {"name": "Normal Adaptive", "beta": 50.0, "alpha": 0.4},
    "G3": {"name": "Peak-Hour Saturation", "density_threshold": 0.8, "G_max": 55.0},
    "R1": {"name": "Standard Red Hold", "R_min": 8.0},
    "R2": {"name": "Opposing Saturation Hold", "fairness_timer": 90.0, "density_threshold": 0.7},
    "E1": {"name": "Single EV Clear Approach", "G_emg": 30.0},
    "E2": {"name": "EV Congested Approach", "G_emg": 55.0},
    "E3": {"name": "Multiple Emergency EVs", "priority_matrix": ["Ambulance", "Fire", "Police"]},
}

# ─── WEATHER VISIBILITY CONFIG (Rule W1) ───
WEATHER_CONFIG = {
    "clear": {"green_factor": 1.0,  "r_min_factor": 1.0},
    "haze":  {"green_factor": 1.15, "r_min_factor": 1.1},
    "rain":  {"green_factor": 1.30, "r_min_factor": 1.2},
    "fog":   {"green_factor": 1.40, "r_min_factor": 1.3},
    "night": {"green_factor": 1.10, "r_min_factor": 1.05},
}

# ─── MUTABLE GLOBAL STATE ───
SIMULATION_TRIGGERED = False
LATEST_FRAMES = {0: b'', 1: b'', 2: b'', 3: b''}
OPPOSING_SATURATION = {i: {"timer": 0, "is_saturated": False} for i in range(4)}
