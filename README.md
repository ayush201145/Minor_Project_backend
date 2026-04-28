# 🚦 CityPulse-X — Intelligent Traffic Signal Simulation

An AI-powered traffic signal management system that uses **YOLOv8 computer vision**, **real-time weather data**, and **adaptive signal timing algorithms** to optimize intersection throughput. Built with a FastAPI backend and React frontend.

---

## ✨ Features

- **Real-Time Vehicle Detection** — YOLOv8m detects and classifies cars, motorcycles, buses, and trucks across 4 lanes simultaneously
- **SORT Object Tracking** — Persistent vehicle tracking with jitter-smoothed bounding boxes and unique vehicle counting
- **Emergency Vehicle Priority** — Dedicated YOLO model detects Ambulances, Fire Engines, and Police Vehicles with a priority matrix (Rule E3)
- **Adaptive Signal Timing** — Green time dynamically adjusts based on lane density, predicted traffic flow, and weather conditions
- **Live Weather Integration** — Real-time weather from OpenWeatherMap API adjusts signal timing (Rule W1) for rain, fog, haze, and night conditions
- **Live Video Feeds** — MJPEG streams of annotated detection frames for all 4 lanes
- **Post-Simulation Analytics** — Final report with vehicle counts, class distribution charts, green time allocation, and emergency event logs

---

## 🏗️ Architecture

```
minor_project/
├── ml_services/                # Backend (FastAPI + YOLO)
│   ├── main.py                 # App entry point + WebSocket simulation engine
│   ├── config.py               # Constants, rules, tuning parameters
│   ├── weather.py              # OpenWeatherMap API client (60s cache)
│   ├── signal_logic.py         # Green time calculator + EV priority resolver
│   ├── perception.py           # Video & geometry helpers
│   ├── routes.py               # REST API endpoints
│   ├── sort.py                 # SORT multi-object tracker
│   ├── yolov8m.pt              # Traffic detection model
│   ├── weights/
│   │   ├── best.pt             # Emergency vehicle detection model
│   │   └── predictor.pkl       # Traffic volume predictor
│   ├── .env                    # API keys (not tracked in git)
│   └── requirements.txt
│
├── frontend/                   # Frontend (React)
│   ├── src/
│   │   ├── App.js              # Main dashboard layout
│   │   ├── App.css             # Global styles
│   │   └── components/
│   │       ├── IntersectionGrid.jsx   # 4-lane video grid with overlays
│   │       ├── WeatherCard.jsx        # Live weather display
│   │       ├── MetricsPanel.jsx       # Real-time analytics
│   │       ├── TrafficLight.jsx       # Signal indicator
│   │       ├── FinalReport.jsx        # Post-simulation report
│   │       └── VideoUploader.jsx      # Video upload handler
│   └── package.json
│
└── .gitignore
```

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **OpenWeatherMap API Key** — [Get one free](https://home.openweathermap.org/users/sign_up)

### 1. Backend Setup

```bash
cd ml_services

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Create a .env file with:
# OWM_API_KEY=your_api_key_here
# DEFAULT_CITY=Patna

# Start the server
python main.py
```

The backend runs at `http://localhost:8000`.

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm start
```

The frontend runs at `http://localhost:3000`.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload` | Upload 4 lane videos to start simulation |
| `GET` | `/weather` | Get current weather data (cached) |
| `POST` | `/set_location` | Change weather city `{"city": "Mumbai"}` |
| `GET` | `/video_feed/{lane_idx}` | MJPEG stream for lane 0-3 |
| `WS` | `/` | WebSocket — real-time simulation data |

---

## 🧠 Signal Timing Rules

| Rule | Name | Trigger |
|------|------|---------|
| **G1** | Off-Peak Low Density | Density < 0.25 → minimum green |
| **G2** | Normal Adaptive | ML-predicted + density-weighted green time |
| **G3** | Peak-Hour Saturation | Density ≥ 0.8 → maximum green hold |
| **E1** | Single EV Clear | Emergency vehicle on low-density lane |
| **E2** | EV Congested | Emergency vehicle on high-density lane |
| **E3** | Multiple EVs | Priority matrix: Ambulance > Fire > Police |
| **W1** | Weather Adjustment | Green time × weather factor (rain: 1.3×, fog: 1.4×) |
| **R1** | Standard Red Hold | Minimum red time enforcement |
| **R2** | Opposing Saturation | Prevents starvation of congested opposing lanes |

---

## 🌦️ Weather Integration

Real-time weather from OpenWeatherMap adjusts signal timing:

| Condition | Green Factor | Red Min Factor |
|-----------|-------------|----------------|
| Clear ☀️ | 1.0× | 1.0× |
| Night 🌙 | 1.1× | 1.05× |
| Haze 🌤️ | 1.15× | 1.1× |
| Rain 🌧️ | 1.3× | 1.2× |
| Fog 🌫️ | 1.4× | 1.3× |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Object Detection** | YOLOv8 (Ultralytics) |
| **Object Tracking** | SORT (Simple Online Realtime Tracking) |
| **Backend** | FastAPI, WebSocket, OpenCV |
| **Weather API** | OpenWeatherMap (free tier) |
| **Frontend** | React 18, Recharts |
| **Streaming** | MJPEG over HTTP |

---

## 📄 License

This project is part of an academic minor project.
