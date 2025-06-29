// src/pages/professor/dashboard/GradingProgress.jsx
import { useEffect, useState } from "react";
import axios from "../../../api/axios";
import "./GradingProgress.css";

export default function GradingProgress() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios
      .get("assignments/grading-progress/")
      .then(res => setRows(res.data))
      .catch(err => console.error("Failed to load grading progress", err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading grading progress…</p>;

  return (
    <div className="grading-progress-container">
      {rows.map((row, idx) => (
        <div key={row.test_id} className="grading-row">
          <div className="grading-tag">{`A${idx + 1}`}</div>

          <div className="grading-info">
            <div className="course-name">{row.test_name}</div>
            <div className="course-meta">
              {row.question_type} • <span>{row.status}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
