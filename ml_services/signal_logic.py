"""
CityPulse-X Signal Logic — Green time calculation and EV priority resolution.
"""

from config import (
    G_min, G_max_peak, BETA, ALPHA, R_min,
    TRAFFIC_RULES, EV_PRIORITY
)


def calc_green(lane_density, p_rho, is_emv, weather_factor=1.0, lane_idx=None):
    """Calculate green time for a lane using rules G1/G2/G3/E1/E2 + weather factor."""
    if is_emv and lane_density < 0.5:
        base = TRAFFIC_RULES["E1"]["G_emg"]
    elif is_emv and lane_density >= 0.5:
        base = TRAFFIC_RULES["E2"]["G_emg"]
    elif lane_density < TRAFFIC_RULES["G1"]["density_threshold"]:
        base = G_min
    elif lane_density >= TRAFFIC_RULES["G3"]["density_threshold"]:
        base = TRAFFIC_RULES["G3"]["G_max"]
    else:
        base = G_min + (BETA * ((ALPHA * lane_density) + ((1.0 - ALPHA) * p_rho)))
    return min(base * weather_factor, G_max_peak)


def select_priority_emergency(emv_lanes, current_ev_types, densities):
    """Resolve which lane gets priority when multiple lanes have emergency vehicles (Rule E3)."""
    best_lane, highest_score = emv_lanes[0], -1
    for lane in emv_lanes:
        lane_max_prio = 0
        for ev_type in current_ev_types[lane]:
            lane_max_prio = max(lane_max_prio, EV_PRIORITY.get(ev_type, 0))
        score = (lane_max_prio * 1000) + densities[lane]
        if score > highest_score:
            highest_score, best_lane = score, lane
    return best_lane
