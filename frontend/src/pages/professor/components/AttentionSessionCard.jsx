import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./AttentionSessionCard.css";

export default function AttentionSessionCard() {
  const [report, setReport] = useState(null);
  const navigate = useNavigate();

  const startSession = () => {
    const sessionId = crypto.randomUUID();
    navigate(`/attention/live?session=${sessionId}`);
  };

  return (
    <div className="attention-session-card">
      <h3>Classroom Attention Monitor</h3>
      <button onClick={startSession} >Start Attention Tracking</button>

      {report && (
        <div className="attention-report">
          <h4>AI Feedback</h4>
          <p><strong>Avg:</strong> {report.avg_attention}%</p>
          <ul>
            {report.advice.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
