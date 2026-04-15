import sys, json, time, os, cv2, glob, pickle, warnings, datetime, math
import numpy as np
import asyncio
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from ultralytics import YOLO

try:
    from sort import Sort
except ImportError:
    print("PY-LOG: SORT module missing.")
    sys.exit(1)

warnings.filterwarnings("ignore")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# System Params
C_i, G_min, G_max_peak, BETA, ALPHA, R_min, FAIRNESS_TIMER = 25.0, 10.0, 55.0, 50.0, 0.4, 8.0, 90.0
K_THRESHOLD, MAX_HOURLY_VOL, CONF_LEVEL = 3, 6000.0, 0.35
JITTER_THRESHOLD, SMOOTHING_FACTOR = 4.0, 0.6  
LANE_MAP = {"lane1": 0, "lane2": 1, "lane3": 2, "lane4": 3}
LANE_PREFIXES = {0: 'N', 1: 'E', 2: 'S', 3: 'W'}

# --- EMERGENCY PRIORITY MATRIX (Rule E3) ---
EV_PRIORITY = {
    "Ambulance": 3,
    "Fire Engine": 2,
    "Police Vehicle": 1
}

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

OPPOSING_SATURATION = {i: {"timer": 0, "is_saturated": False} for i in range(4)}

# --- GLOBAL STATES ---
SIMULATION_TRIGGERED = False
LATEST_FRAMES = {0: b'', 1: b'', 2: b'', 3: b''}

def get_latest_video(v_dir, lid):
    files = glob.glob(os.path.join(v_dir, f"{lid}*.mp4"))
    return max(files, key=os.path.getmtime) if files else None

def calc_green(lane_density, p_rho, is_emv, lane_idx=None):
    if is_emv and lane_density < 0.5: return TRAFFIC_RULES["E1"]["G_emg"]
    if is_emv and lane_density >= 0.5: return TRAFFIC_RULES["E2"]["G_emg"]
    if lane_density < TRAFFIC_RULES["G1"]["density_threshold"]: return G_min
    if lane_density >= TRAFFIC_RULES["G3"]["density_threshold"]: return TRAFFIC_RULES["G3"]["G_max"]
    g_adaptive = G_min + (BETA * ((ALPHA * lane_density) + ((1.0 - ALPHA) * p_rho)))
    return min(g_adaptive, G_max_peak)

def select_priority_emergency(emv_lanes, current_ev_types, densities):
    best_lane, highest_score = emv_lanes[0], -1
    for lane in emv_lanes:
        lane_max_prio = 0
        for ev_type in current_ev_types[lane]:
            lane_max_prio = max(lane_max_prio, EV_PRIORITY.get(ev_type, 0))
        score = (lane_max_prio * 1000) + densities[lane]
        if score > highest_score:
            highest_score, best_lane = score, lane
    return best_lane

def calc_centroid(box): return (box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0

# --- ENDPOINTS ---
@app.post("/upload")
async def upload_endpoint(request: Request):
    global SIMULATION_TRIGGERED
    form = await request.form()
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    for old_file in glob.glob(os.path.join(upload_dir, "*.mp4")):
        try: os.remove(old_file)
        except Exception: pass
    for field_name, file_obj in form.items():
        if hasattr(file_obj, 'filename') and file_obj.filename:
            with open(os.path.join(upload_dir, f"{field_name}_{int(time.time())}.mp4"), "wb") as buffer:
                buffer.write(await file_obj.read())
    SIMULATION_TRIGGERED = True 
    return {"status": "success", "message": "Engine started"}

@app.get("/video_feed/{lane_idx}")
async def video_feed(lane_idx: int):
    async def frame_generator(lane_idx):
        while True:
            frame_bytes = LATEST_FRAMES.get(lane_idx)
            if frame_bytes:
                yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            await asyncio.sleep(0.05)
    return StreamingResponse(frame_generator(lane_idx), media_type="multipart/x-mixed-replace; boundary=frame")

# --- MAIN AI & WEBSOCKET ENGINE ---
@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    global SIMULATION_TRIGGERED, LATEST_FRAMES
    await websocket.accept()
    bd = os.path.dirname(os.path.abspath(__file__))
    
    t_model, a_model = YOLO('yolov8m.pt'), YOLO(os.path.join(bd, 'weights', 'best.pt'))
    try:
        with open(os.path.join(bd, 'weights', 'predictor.pkl'), 'rb') as f: pred = pickle.load(f)
    except Exception: pred = None

    v_dir = os.path.join(bd, "uploads")
    os.makedirs(v_dir, exist_ok=True)

    try:
        while True:
            if not SIMULATION_TRIGGERED:
                await asyncio.sleep(0.5)
                continue
                
            SIMULATION_TRIGGERED = False
            caps, curr_files, finished = {}, {}, [False] * 4
            tot_veh, emv_cnts, emv_buf, p_rho = [0]*4, [0]*4, [0]*4, [0.0]*4
            cls_mat = {c: [0]*4 for c in ["car", "motorcycle", "bus", "truck"]}
            trackers = [Sort(max_age=20, min_hits=3, iou_threshold=0.3) for _ in range(4)]
            stable_boxes, unique_vehicles = [{} for _ in range(4)], [set() for _ in range(4)]
            act_lane, last_sw, start_t, last_rec = 0, time.time(), time.time(), 0
            cached_frames, cached_dens, frames_read = [None]*4, [0.0]*4, [0]*4
            last_raw_frames = [None] * 4 
            
            # --- NEW: Stopwatch array to track real cumulative green time ---
            total_green_time = [0.0] * 4
            last_tick = time.time()

            while not all(finished):
                if SIMULATION_TRIGGERED: 
                    for cap in caps.values():
                        if cap: cap.release()
                    break 
                
                dens = [0.0] * 4
                current_ev_types = {0: set(), 1: set(), 2: set(), 3: set()}

                # --- PERCEPTION ---
                for lid, idx in LANE_MAP.items():
                    if finished[idx]: continue

                    if frames_read[idx] > 5 and act_lane != idx:
                        dens[idx] = cached_dens[idx]
                        if cached_frames[idx] is not None:
                            LATEST_FRAMES[idx] = cached_frames[idx]
                        continue

                    vp = get_latest_video(v_dir, lid)
                    if vp != curr_files.get(lid): 
                        if caps.get(lid): caps[lid].release()
                        caps[lid], curr_files[lid] = cv2.VideoCapture(vp), vp

                    ret, frame = caps[lid].read() if caps.get(lid) else (False, None)
                    if not ret: 
                        finished[idx] = True
                        if last_raw_frames[idx] is not None:
                            end_frame = last_raw_frames[idx].copy()
                            end_frame = cv2.addWeighted(end_frame, 0.5, np.zeros_like(end_frame), 0.5, 0)
                            text = "VIDEO ENDS"
                            font = cv2.FONT_HERSHEY_SIMPLEX
                            text_size = cv2.getTextSize(text, font, 1.5, 4)[0]
                            cv2.putText(end_frame, text, ((end_frame.shape[1]-text_size[0])//2, (end_frame.shape[0]+text_size[1])//2), font, 1.5, (0, 0, 255), 4)
                            ret_enc, buffer = cv2.imencode('.jpg', end_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                            if ret_enc: LATEST_FRAMES[idx] = buffer.tobytes()
                        continue 

                    last_raw_frames[idx] = frame.copy()
                    frames_read[idx] += 1
                    
                    t_res = t_model(frame, stream=True, verbose=False, conf=CONF_LEVEL, classes=[2,3,5,7])
                    detections, det_labels = np.empty((0, 5)), {} 
                    for r in t_res:
                        for b in r.boxes:
                            x1, y1, x2, y2 = b.xyxy[0].cpu().numpy()
                            cls_name = t_model.names[int(b.cls[0].item())]
                            detections = np.vstack((detections, np.array([x1, y1, x2, y2, b.conf[0].item()])))
                            det_labels[(int(x1), int(y1))] = cls_name 

                    tracked_objects = trackers[idx].update(detections)
                    current_raw_dens = min(1.0, float(len(tracked_objects)) / C_i)
                    dens[idx] = (0.85 * cached_dens[idx]) + (0.15 * current_raw_dens) if cached_dens[idx] > 0.0 else current_raw_dens

                    for track in tracked_objects:
                        x1, y1, x2, y2, trk_id = track
                        trk_id, curr_box = int(trk_id), (x1, y1, x2, y2)
                        c_name = "car"
                        for (dx, dy), label in det_labels.items():
                            if abs(dx - x1) < 25 and abs(dy - y1) < 25: c_name = label; break
                        
                        if trk_id in stable_boxes[idx]:
                            px1, py1, px2, py2 = stable_boxes[idx][trk_id]
                            x1 = (SMOOTHING_FACTOR * x1) + ((1.0 - SMOOTHING_FACTOR) * px1)
                            y1 = (SMOOTHING_FACTOR * y1) + ((1.0 - SMOOTHING_FACTOR) * py1)
                            x2 = (SMOOTHING_FACTOR * x2) + ((1.0 - SMOOTHING_FACTOR) * px2)
                            y2 = (SMOOTHING_FACTOR * y2) + ((1.0 - SMOOTHING_FACTOR) * py2)
                        stable_boxes[idx][trk_id] = (x1, y1, x2, y2)

                        if trk_id not in unique_vehicles[idx]:
                            unique_vehicles[idx].add(trk_id)
                            tot_veh[idx] += 1
                            if c_name in cls_mat: cls_mat[c_name][idx] += 1

                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 204), 2)
                        cv2.putText(frame, f"{c_name.upper()} {LANE_PREFIXES[idx]}{trk_id}", (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 204), 2)

                    a_res = a_model(frame, verbose=False, conf=0.60)[0]
                    if len(a_res.boxes) > 0:
                        emv_buf[idx] += 1
                        for b in a_res.boxes:
                            ax1, ay1, ax2, ay2 = b.xyxy[0].cpu().numpy()
                            ev_name = a_model.names[int(b.cls[0].item())] 
                            current_ev_types[idx].add(ev_name)
                            color = (62, 62, 255)
                            if ev_name == 'Fire Engine': color = (0, 165, 255)
                            elif ev_name == 'Police Vehicle': color = (255, 0, 0)
                            cv2.rectangle(frame, (int(ax1), int(ay1)), (int(ax2), int(ay2)), color, 3)
                            cv2.putText(frame, ev_name.upper(), (int(ax1), int(ay1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                    else:
                        emv_buf[idx] = max(0, emv_buf[idx] - 1)
                        
                    if emv_buf[idx] == K_THRESHOLD: emv_cnts[idx] += 1

                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if ret:
                        cached_frames[idx] = buffer.tobytes()
                        LATEST_FRAMES[idx] = cached_frames[idx]
                    cached_dens[idx] = dens[idx]

                # --- SSM (Signal State Management) ---
                now = time.time()
                
                # NEW: Calculate the exact loop duration and add it to the active lane's total time
                loop_dt = now - last_tick
                last_tick = now
                total_green_time[act_lane] += loop_dt
                
                elapsed = int(now - start_t)
                
                if elapsed > last_rec:
                    if pred:
                        dt = datetime.datetime.now()
                        p_rho = [max(0.0, min(1.0, float(pred.predict([[dt.weekday(), dt.hour]])[0]) / MAX_HOURLY_VOL))] * 4
                    else:
                        p_rho = [(ALPHA * dens[i]) + ((1-ALPHA) * p_rho[i]) for i in range(4)]
                    last_rec = elapsed

                for lane in range(4):
                    if OPPOSING_SATURATION[lane]["timer"] > 0: OPPOSING_SATURATION[lane]["timer"] -= 1
                    else: OPPOSING_SATURATION[lane]["is_saturated"] = False

                t_diff = now - last_sw
                emvs = [i for i, b in enumerate(emv_buf) if b >= K_THRESHOLD]
                tgt = act_lane
                
                if emvs:
                    tgt = select_priority_emergency(emvs, current_ev_types, dens)
                    g_max = calc_green(dens[tgt], p_rho[tgt], True, tgt)
                else:
                    g_max = calc_green(dens[act_lane], p_rho[act_lane], False, act_lane)
                    best_lane = dens.index(max(dens))
                    opposing_idx = (act_lane + 2) % 4 
                    waiting_lanes = [i for i in range(4) if i != act_lane]
                    next_best_lane = max(waiting_lanes, key=lambda i: dens[i])
                    
                    if OPPOSING_SATURATION[opposing_idx]["is_saturated"] and dens[opposing_idx] >= TRAFFIC_RULES["R2"]["density_threshold"]:
                        tgt = act_lane
                    elif dens[act_lane] == 0.0 and t_diff >= R_min:
                        tgt = best_lane if sum(dens) > 0 else (act_lane + 1) % 4
                    elif best_lane != act_lane and t_diff >= G_min:
                        if (dens[best_lane] - dens[act_lane]) >= 0.08: tgt = best_lane
                        elif t_diff >= g_max: tgt = best_lane
                    elif best_lane == act_lane and t_diff >= g_max:
                        if dens[next_best_lane] > 0: tgt = next_best_lane
                        else: t_diff = 0.0 

                if tgt != act_lane and (t_diff >= R_min or emvs or finished[act_lane]):
                    act_lane, last_sw, t_diff = tgt, now, 0.0
                    g_max = calc_green(dens[act_lane], p_rho[act_lane], act_lane in emvs, act_lane)

                await websocket.send_json({
                    "status": "EMERGENCY" if emvs else "NORMAL",
                    "active_lane": act_lane, 
                    "timer": int(max(0, g_max - t_diff)),
                    "densities": dens,
                    "applied_rules": {
                        "green_rule": "G1" if dens[act_lane] < 0.25 else ("G3" if dens[act_lane] >= 0.8 else "G2"),
                        "emergency_rule": "E3" if len(emvs) > 1 else ("E2" if emvs and dens[act_lane] >= 0.5 else ("E1" if emvs else None))
                    }
                })
                await asyncio.sleep(0.05)
            
            # --- POST-SIMULATION CLEANUP ---
            if all(finished) and not SIMULATION_TRIGGERED:
                await websocket.send_json({
                    "status": "SIMULATION_COMPLETE", 
                    "final_stats": {
                        "total_vehicles": tot_veh, 
                        "emergencies": emv_cnts, 
                        "class_matrix": cls_mat, 
                        # Return the actual tracked seconds instead of a calculation
                        "green_times": [int(total_green_time[i]) for i in range(4)]
                    }
                })
                
                for cap in caps.values():
                    if cap: cap.release()
                print("PY-LOG: Simulation Complete. Purging video uploads...")
                for vp in set(curr_files.values()):
                    if vp and os.path.exists(vp):
                        try: os.remove(vp)
                        except Exception as e: pass

    except WebSocketDisconnect: pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)