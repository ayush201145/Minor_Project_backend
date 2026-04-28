import React from 'react';

const CONDITION_THEME = {
    clear: { icon: '☀️', gradient: 'linear-gradient(135deg, #f59e0b22, #f9731611)', border: '#f59e0b44' },
    haze:  { icon: '🌤️', gradient: 'linear-gradient(135deg, #d2992222, #a3730011)', border: '#d2992244' },
    rain:  { icon: '🌧️', gradient: 'linear-gradient(135deg, #60a5fa22, #3b82f611)', border: '#60a5fa44' },
    fog:   { icon: '🌫️', gradient: 'linear-gradient(135deg, #9ca3af22, #6b728011)', border: '#9ca3af44' },
    night: { icon: '🌙', gradient: 'linear-gradient(135deg, #818cf822, #6366f111)', border: '#818cf844' },
};

const WeatherCard = ({ weather }) => {
    if (!weather || !weather.condition) return null;

    const theme = CONDITION_THEME[weather.condition] || CONDITION_THEME.clear;
    const iconUrl = weather.icon
        ? `https://openweathermap.org/img/wn/${weather.icon}@2x.png`
        : null;

    return (
        <div className="weather-card" style={{ background: theme.gradient, borderColor: theme.border }}>
            <div className="weather-card-header">
                <div className="weather-card-location">
                    <span className="weather-card-city">{weather.city || 'Unknown'}</span>
                    <span className="weather-card-desc">{weather.description || 'N/A'}</span>
                </div>
                {iconUrl && (
                    <img 
                        className="weather-card-icon" 
                        src={iconUrl} 
                        alt={weather.description}
                    />
                )}
            </div>

            <div className="weather-card-temp">
                {weather.temp !== undefined ? `${Math.round(weather.temp)}°` : '--°'}
                <span className="weather-card-feels">
                    Feels {weather.feels_like !== undefined ? `${Math.round(weather.feels_like)}°` : '--°'}
                </span>
            </div>

            <div className="weather-card-metrics">
                <div className="weather-metric">
                    <span className="weather-metric-icon">💧</span>
                    <span className="weather-metric-val">{weather.humidity ?? '--'}%</span>
                    <span className="weather-metric-label">Humidity</span>
                </div>
                <div className="weather-metric">
                    <span className="weather-metric-icon">💨</span>
                    <span className="weather-metric-val">{weather.wind_speed ?? '--'} m/s</span>
                    <span className="weather-metric-label">Wind</span>
                </div>
                <div className="weather-metric">
                    <span className="weather-metric-icon">👁️</span>
                    <span className="weather-metric-val">{weather.visibility ? `${(weather.visibility / 1000).toFixed(1)}km` : '--'}</span>
                    <span className="weather-metric-label">Visibility</span>
                </div>
            </div>
        </div>
    );
};

export default WeatherCard;
