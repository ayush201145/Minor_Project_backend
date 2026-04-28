import React from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const COLORS = ['#58a6ff', '#3fb950', '#d29922', '#f85149'];
const DIRS = ['North', 'East', 'South', 'West'];

const FinalReport = ({ stats }) => {
  if (!stats) return null;

  // Internal helper to format chart data
  const getChartData = () => {
    return DIRS.map((dir, i) => ({
      name: dir,
      value: stats.total_vehicles[i]
    }));
  };

  // Internal helper to find the busiest lane
  const getCriticalLane = () => {
    if (!stats.total_vehicles || stats.total_vehicles.length === 0) {
      return { name: "Unknown", val: 0 };
    }
    const maxVal = Math.max(...stats.total_vehicles);
    const maxIdx = stats.total_vehicles.indexOf(maxVal);
    return { name: DIRS[maxIdx] || "Unknown", val: maxVal };
  };

  const critical = getCriticalLane();

  return (
    <div className="stats-overlay">
      {/* 1. Critical Priority Section */}
      <div className="critical-box">
        <h4>🏆 Critical Priority Direction</h4>
        <h1 className="critical-text">{critical.name.toUpperCase()}</h1>
        <p>{critical.val} vehicles detected • <span className="red-text">Highest Traffic Volume</span></p>
      </div>

      {/* 2. Visual Charts Row */}
      <div className="charts-row">
        <div className="chart-card">
          <h3>Vehicle Count by Direction</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={getChartData()}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
              <XAxis dataKey="name" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip contentStyle={{ backgroundColor: '#111', borderColor: '#333' }} />
              <Bar dataKey="value" fill="#58a6ff" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Traffic Share Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie 
                data={getChartData()} 
                cx="50%" cy="50%" 
                innerRadius={0} 
                outerRadius={80} 
                dataKey="value" 
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
              >
                {getChartData().map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#111', borderColor: '#333' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 3. Classification Table */}
      <div className="table-card">
        <h3>🚗 Vehicle Classification Matrix</h3>
        <table className="custom-table">
          <thead>
            <tr>
              <th></th>
              {DIRS.map(d => <th key={d}>{d}</th>)}
            </tr>
          </thead>
          <tbody>
            {Object.keys(stats.class_matrix).map(vehicle => (
              <tr key={vehicle}>
                <td style={{ textTransform: 'capitalize' }}>{vehicle}</td>
                {stats.class_matrix[vehicle].map((val, i) => (
                  <td key={i}>{val}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 4. Cumulative Signal Timings Table */}
      <div className="table-card">
        <h3>⏱️ Cumulative Signal Usage</h3>
        <p style={{ color: '#888', marginBottom: '15px', fontSize: '12px' }}>
          Total green light duration and emergency vehicle clearances
        </p>
        <table className="custom-table">
          <thead>
            <tr>
              <th>Direction</th>
              <th>Green Time (sec)</th>
              <th>Emergencies Cleared</th>
            </tr>
          </thead>
          <tbody>
            {DIRS.map((dir, i) => (
              <tr key={dir}>
                <td><strong>{dir}</strong></td>
                <td>
                  <div className="progress-bar-container">
                    <div 
                        className="progress-bar" 
                        style={{ 
                            width: `${Math.min(100, (stats.green_times[i] / Math.max(...stats.green_times)) * 100)}%`, 
                            backgroundColor: stats.emergencies[i] > 0 ? '#ff4444' : '#3fb950' 
                        }}
                    ></div>
                    <span className="progress-val">{stats.green_times[i]}s</span>
                  </div>
                </td>
                <td style={{ color: stats.emergencies[i] > 0 ? '#ff4444' : '#888', fontWeight: stats.emergencies[i] > 0 ? 'bold' : 'normal' }}>
                  {stats.emergencies[i] > 0 ? `🚑 ${stats.emergencies[i]} Cleared` : 'None'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default FinalReport;