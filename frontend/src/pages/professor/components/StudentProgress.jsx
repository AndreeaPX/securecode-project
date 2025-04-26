import React from "react";
import "./StudentProgress.css";

const moksSet = [
    { name: "Johen", progress: 84 },
    { name: "Aneesha", progress: 64 },
    { name: "Josna", progress: 54 },
    { name: "Dhanush", progress: 44 },
];

export default function StudentProgress(){
    return(
        <div className="student-progress-container">
        {moksSet.map((student, index) => (
          <div key={index} className="student-row">
            <div className="student-info">
              <div className="avatar-placeholder">{student.name[0]}</div>
              <span>{student.name}</span>
            </div>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${student.progress}%` }}
              ></div>
            </div>
            <span className="progress-value">{student.progress}%</span>
          </div>
        ))}
      </div>
    );
}