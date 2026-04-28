import React from 'react';

const MetricsPanel = ({ metrics }) => {
  const data = metrics || {
    status: "STANDBY",
    active_lane: null,
    timer: 0,
    densities: [0, 0, 0, 0],
    applied_rules: null
  };

  const isEmergency = data.status === "EMERGENCY";
  const rules = data.applied_rules;

  const ruleNames = {
    "G1": "Off-Peak Low Density (Fast Cycle)",
    "G2": "Normal Adaptive (ML Predicted)",
    "G3": "Peak-Hour Saturation (Max Hold)",
    "E1": "Single EV Clear Approach",
    "E2": "EV Congested Approach",
    "E3": "Multiple EVs (Priority Matrix)"
  };

  return (
    <div style={styles.panel}>
      <h2 style={styles.title}>CityPulse-X Analytics</h2>
      
      {/* Dynamic Status Banner */}
      <div style={styles.statusBanner(isEmergency)}>
        <strong>System Status: </strong> 
        {data.status}
      </div>

      <div style={styles.grid}>
        <div style={styles.card}>
          <div style={styles.cardLabel}>Active Green Signal</div>
          <div style={styles.primaryValue}>
            {data.active_lane !== null ? `Lane ${data.active_lane + 1}` : "-"}
          </div>
        </div>
        
        <div style={styles.card}>
          <div style={styles.cardLabel}>Time Remaining</div>
          <div style={styles.primaryValue}>
            {data.timer} <span style={{fontSize: '1rem'}}>sec</span>
          </div>
        </div>
      </div>

      {rules && (
        <>
          <h3 style={styles.subtitle}>Active AI Directives</h3>
          <div style={styles.rulesContainer}>
            <div style={styles.ruleBadge('green')}>
               <span style={styles.ruleCode}>{rules.green_rule}</span>
               <span style={styles.ruleDesc}>{ruleNames[rules.green_rule] || "Adaptive Mode"}</span>
            </div>
            
            {rules.emergency_rule && (
              <div style={styles.ruleBadge('emergency')}>
                 <span style={styles.ruleCode}>{rules.emergency_rule}</span>
                 <span style={styles.ruleDesc}>{ruleNames[rules.emergency_rule]}</span>
              </div>
            )}
          </div>
        </>
      )}

      <h3 style={styles.subtitle}>Live Intersection Density (EMA)</h3>
      <div style={styles.densityGrid}>
        {data.densities.map((count, index) => {
          const isActive = data.active_lane === index;
          const displayCount = typeof count === 'number' ? count.toFixed(2) : "0.00";
          
          return (
            <div key={index} style={styles.densityCard(isActive)}>
              <div style={styles.laneHeader}>{['NORTH', 'EAST', 'SOUTH', 'WEST'][index]}</div>
              <div style={styles.densityValue}>{displayCount}</div>
              <div style={styles.laneLabel}>capacity ratio</div>
              {isActive && <div style={styles.activeIndicator}>GREEN</div>}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const styles = {
  panel: {
    backgroundColor: '#1e293b', color: '#f8fafc', padding: '24px', borderRadius: '12px',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)', fontFamily: 'system-ui, -apple-system, sans-serif',
    maxWidth: '500px', margin: '0 auto'
  },
  title: { margin: '0 0 20px 0', fontSize: '1.5rem', fontWeight: 'bold', borderBottom: '1px solid #334155', paddingBottom: '10px' },
  statusBanner: (isEmergency) => ({
    backgroundColor: isEmergency ? '#ef4444' : '#10b981',
    color: '#fff', padding: '12px', borderRadius: '8px', textAlign: 'center', marginBottom: '24px',
    fontWeight: '600', letterSpacing: '1px', animation: isEmergency ? 'pulse 1.5s infinite' : 'none'
  }),
  grid: { display: 'flex', gap: '16px', marginBottom: '24px' },
  card: { flex: 1, backgroundColor: '#0f172a', padding: '16px', borderRadius: '8px', textAlign: 'center', border: '1px solid #334155' },
  cardLabel: { fontSize: '0.875rem', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '8px' },
  primaryValue: { fontSize: '2rem', fontWeight: 'bold', color: '#38bdf8' },
  subtitle: { fontSize: '1.1rem', marginBottom: '12px', marginTop: '20px', color: '#cbd5e1', borderBottom: '1px solid #334155', paddingBottom: '8px' },
  rulesContainer: { display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '24px' },
  ruleBadge: (type) => {
    let bg = '#0f172a'; let border = '#334155'; let text = '#64748b'; 
    if (type === 'green') { bg = '#064e3b'; border = '#10b981'; text = '#34d399'; }
    if (type === 'emergency') { bg = '#7f1d1d'; border = '#ef4444'; text = '#fca5a5'; }
    return { display: 'flex', alignItems: 'center', backgroundColor: bg, border: `1px solid ${border}`, padding: '8px 12px', borderRadius: '6px', color: text, fontSize: '0.875rem' };
  },
  ruleCode: { fontWeight: 'bold', marginRight: '12px', paddingRight: '12px', borderRight: '1px solid currentColor', fontSize: '1rem', minWidth: '25px', textAlign: 'center' },
  ruleDesc: { flex: 1 },
  densityGrid: { display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' },
  densityCard: (isActive) => ({ backgroundColor: isActive ? '#064e3b' : '#334155', border: isActive ? '2px solid #10b981' : '2px solid transparent', padding: '16px', borderRadius: '8px', textAlign: 'center', position: 'relative' }),
  laneHeader: { fontWeight: 'bold', color: '#f1f5f9', marginBottom: '8px', letterSpacing: '1px' },
  densityValue: { fontSize: '1.75rem', fontWeight: 'bold', color: '#fff' },
  laneLabel: { fontSize: '0.75rem', color: '#94a3b8' },
  activeIndicator: { position: 'absolute', top: '8px', right: '8px', fontSize: '0.65rem', backgroundColor: '#10b981', color: '#fff', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }
};

export default MetricsPanel;