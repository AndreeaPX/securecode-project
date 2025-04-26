export default function BiometricSummary() {
  const data = {
    keystrokes: 32,
    focusLost: 14,
    copyPaste: 2,
    anomalyScore: 0.62,
  };

  const getAnomalyLevel = (score) => {
    if (score > 0.7) return "High Risk";
    if (score > 0.4) return "Moderate Risk";
    return "Low Risk";
  };

  const getRiskClass = (score) => {
    if (score > 0.7) return "risk-high";
    if (score > 0.4) return "risk-moderate";
    return "risk-low";
  };

  return (
    <div className="stat-card">
      <h3 className="card-title">Biometric Summary</h3>
      <ul>
        <li><strong>Avg Keystrokes per Answer:</strong> {data.keystrokes}</li>
        <li><strong>Focus Lost Events:</strong> {data.focusLost} total</li>
        <li><strong>Copy/Paste Attempts:</strong> {data.copyPaste}</li>
        <li><strong>Avg Anomaly Score:</strong> {data.anomalyScore}</li>
        <li>
          <strong>Risk Level: </strong>
          <span className={getRiskClass(data.anomalyScore)}>
            {getAnomalyLevel(data.anomalyScore)}
          </span>
        </li>
      </ul>
    </div>
  );
}
