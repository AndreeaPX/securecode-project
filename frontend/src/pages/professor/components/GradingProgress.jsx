import React from "react";
import "./GradingProgress.css";

const mockCourses = [
  { course: "Multimedia Course", type: "Multiple Choice", status: "AI Corrected" },
  { course: "JAVA Course", type: "Open Response", status: "Cristian Ionita" },
];

export default function GradingProgress() {
  return (
    <div className="grading-progress-container">
      {mockCourses.map((course, index) => (
        <div key={index} className="grading-row">
          <div className="grading-tag">{`A${index + 1}`}</div>
          <div className="grading-info">
            <div className="course-name">{course.course}</div>
            <div className="course-meta">
              {course.type} • <span>{course.status}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
