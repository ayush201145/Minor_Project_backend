import React, { useState, useRef } from 'react';
import './App.css';
import IntersectionGrid from './components/IntersectionGrid';
import FinalReport from './components/FinalReport';
import WeatherCard from './components/WeatherCard';

const DIRS = ['North', 'East', 'South', 'West'];

function App() {
  const [simData, setSimData] = useState({ 
    status: "WAITING", active_lane: 0, timer: 0, 
    densities: [0,0,0,0], final_stats: null,
    weather: null
  });
  const [videoFiles, setVideoFiles] = useState([null, null, null, null]);
  const [isConnected, setIsConnected] = useState(false);
  const [cityInput, setCityInput] = useState('Patna');
  const [cityLoading, setCityLoading] = useState(false);
  const ws = useRef(null);

  const handleFile = (index, e) => {
    const newFiles = [...videoFiles];
    newFiles[index] = e.target.files[0];
    setVideoFiles(newFiles);
  };

  const handleSetCity = async () => {
    if (!cityInput.trim()) return;
    setCityLoading(true);
    try {
      const res = await fetch("http://localhost:8000/set_location", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ city: cityInput.trim() })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.weather) {
          setSimData(prev => ({ ...prev, weather: data.weather }));
        }
      }
    } catch (err) {
      console.warn("Failed to set city:", err);
    }
    setCityLoading(false);
  };

  const startSimulation = async () => {
    if (videoFiles.includes(null)) return alert("Upload all 4 videos first.");
    const formData = new FormData();
    videoFiles.forEach((file, i) => formData.append(`lane${i+1}`, file));

    try {
      const res = await fetch("http://localhost:8000/upload", { method: "POST", body: formData });
      if (res.ok) {
        ws.current = new WebSocket('ws://localhost:8000');
        ws.current.onopen = () => setIsConnected(true);
        ws.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setSimData(data);
            if (data.status === "SIMULATION_COMPLETE") ws.current.close();
          } catch (err) {
            console.warn("⚠️ Dropped incomplete WS frame");
          }
        };
        ws.current.onclose = () => setIsConnected(false);
      }
    } catch (err) { alert("Upload failed. Ensure backend is running."); }
  };

  const getStatusClass = () => {
    if (simData.status === "WAITING") return "status-waiting";
    if (simData.status === "EMERGENCY") return "status-emergency";
    if (simData.status === "SIMULATION_COMPLETE") return "status-complete";
    return "status-normal";
  };

  const getButtonLabel = () => {
    if (simData.status === "SIMULATION_COMPLETE") return "RESET";
    return "START ENGINE";
  };

  const handleButtonClick = () => {
    if (simData.status === "SIMULATION_COMPLETE") {
      window.location.reload();
    } else {
      startSimulation();
    }
  };

  return (
    <div className="dashboard">
      <div className="sidebar">
        {/* Brand */}
        <div className="brand">
          <span className="brand-icon">
            <span className="brand-dot-red"></span>
            <span className="brand-dot-yellow"></span>
          </span>
          CityPulse-X
        </div>

        {/* System Status Card */}
        <div className="card">
          <div className="card-header">SYSTEM STATUS</div>
          <span className={`status-text ${getStatusClass()}`}>
            {simData.status}
          </span>
        </div>

        {/* City Selector */}
        <div className="card">
          <div className="card-header">WEATHER LOCATION</div>
          <div className="city-selector">
            <input 
              type="text"
              className="city-input"
              value={cityInput}
              onChange={(e) => setCityInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSetCity()}
              placeholder="Enter city name..."
            />
            <button 
              className="city-btn"
              onClick={handleSetCity}
              disabled={cityLoading}
            >
              {cityLoading ? '...' : '📍'}
            </button>
          </div>
        </div>

        {/* Live Weather Card */}
        <WeatherCard weather={simData.weather} />

        {/* Feed Config */}
        {!isConnected && simData.status !== "SIMULATION_COMPLETE" && (
          <div className="card">
            <div className="feed-config-title">Feed Config</div>
            {DIRS.map((dir, i) => (
              <div key={dir} className="upload-group">
                <label className="upload-group-label">{dir} Lane</label>
                <div className="file-input-wrapper">
                  <span className={`file-input-display ${videoFiles[i] ? 'has-file' : ''}`}>
                    {videoFiles[i] ? videoFiles[i].name : 'Choose Video (Max 500MB)'}
                  </span>
                  <input 
                    type="file" 
                    accept="video/mp4,video/*"
                    onChange={(e) => handleFile(i, e)} 
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Start Engine / Reset Button */}
        <button 
          className={`btn ${simData.status === "SIMULATION_COMPLETE" ? "btn-danger" : "btn-primary"}`}
          onClick={handleButtonClick} 
          disabled={isConnected}
        >
          {getButtonLabel()}
        </button>
      </div>

      <div className="main-stage">
        {simData.status === "SIMULATION_COMPLETE" ? (
          /* PASS STATS TO THE NEW COMPONENT */
          <FinalReport stats={simData.final_stats} />
        ) : (
          <IntersectionGrid simData={simData} videoFiles={videoFiles} />
        )}
      </div>
    </div>
  );
}

export default App;