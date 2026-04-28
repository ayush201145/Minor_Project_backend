import React from 'react';

const DIRS = ['NORTH', 'EAST', 'SOUTH', 'WEST'];

const WEATHER_DISPLAY = {
    clear: { icon: '☀️', label: 'Clear',  color: '#fbbf24' },
    haze:  { icon: '🌤️', label: 'Haze',   color: '#d29922' },
    rain:  { icon: '🌧️', label: 'Rain',   color: '#60a5fa' },
    fog:   { icon: '🌫️', label: 'Fog',    color: '#9ca3af' },
    night: { icon: '🌙', label: 'Night',  color: '#818cf8' },
};

const IntersectionGrid = ({ simData }) => {
    return (
        <div className="grid-container">
            {[0, 1, 2, 3].map((i) => {
                const isActive = simData?.active_lane === i;
                const timer = simData?.timer || 0;
                
                const streamUrl = simData.status !== "WAITING" 
                    ? `http://localhost:8000/video_feed/${i}` 
                    : null;

                const displayDensity = simData.densities?.[i] !== undefined 
                    ? simData.densities[i].toFixed(2) 
                    : "0.00";

                // Weather is now a single object from API, same for all lanes
                const weatherCondition = simData.weather?.condition || "clear";
                const weatherInfo = WEATHER_DISPLAY[weatherCondition] || WEATHER_DISPLAY.clear;

                return (
                    <div 
                        key={i} 
                        className={`video-box ${isActive && simData.status !== "WAITING" ? 'active-feed' : ''}`}
                    >
                        {/* Video Feed or Offline Placeholder */}
                        {streamUrl ? (
                            <img 
                                src={streamUrl} 
                                alt={`Lane ${i + 1} Feed`}
                            />
                        ) : (
                            <div className="feed-offline">
                                <div className="feed-offline-icon">📡</div>
                                <div className="feed-offline-text">
                                    {`Feed ${i + 1} Offline`}
                                </div>
                            </div>
                        )}

                        {/* Weather Badge - Top Left */}
                        <div className="weather-badge">
                            <span className="weather-icon">{weatherInfo.icon}</span>
                            <span className="weather-label" style={{ color: weatherInfo.color }}>
                                {weatherInfo.label}
                            </span>
                        </div>
                        
                        {/* Density Badge - Top Right */}
                        <div className="density-badge">
                            <span className="density-label">DENSITY:</span>
                            <span className="density-value">{displayDensity}</span>
                        </div>

                        {/* Direction Label - Bottom Left */}
                        <div className="direction-label">
                            <span className="direction-name">{DIRS[i]}</span>
                            <span className={`signal-dot ${isActive ? 'green' : 'red'}`}></span>
                            <span className={`signal-timer ${isActive ? 'active' : 'waiting'}`}>
                                {isActive ? `${timer}s` : 'WAIT'}
                            </span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

export default IntersectionGrid;