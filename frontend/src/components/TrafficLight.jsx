import React from 'react';

const TrafficLight = ({ isActive, timer, density, index }) => {
    return (
        <div style={{ padding: '10px', background: '#222', color: 'white', borderRadius: '8px', marginTop: '10px' }}>
            <h3>Lane {index + 1}</h3>
            <h2 style={{ color: isActive ? '#00ff00' : '#ff0000' }}>{isActive ? '🟢 GREEN' : '🔴 RED'}</h2>
            {isActive && <p>Time Remaining: <strong>{timer}</strong></p>}
            <p>Clustered Density Score: {density}</p>
        </div>
    );
};
export default TrafficLight;