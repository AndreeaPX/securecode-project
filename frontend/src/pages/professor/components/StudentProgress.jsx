import React, { useEffect, useState } from "react";
import axiosInstance from "../../../api/axios";
import "./StudentProgress.css";

export default function StudentProgress() {
  const [progressList, setProgressList] = useState([]);

  useEffect(() => {
    axiosInstance.get("/assignments/progress/")
      .then(res => setProgressList(res.data))
      .catch(err => console.error("Failed to fetch progress", err));
  }, []);

  return (
    <div className="student-progress-container">
      {progressList.map((assignment, index) => (
        <div key={assignment.id} className="student-row">
          <div className="student-info">
            <div className="avatar-placeholder">
              {index + 1}
            </div>
            <span>{assignment.name}</span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${assignment.progress_percent}%` }}
            ></div>
          </div>
          <span className="progress-value">{assignment.progress_percent}%</span>
        </div>
      ))}
    </div>
  );
}
