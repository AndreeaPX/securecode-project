import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axiosInstance from "../../../api/axios";
import "../../../styles/StudentCourseTest.css";

export default function StudentCourseTest() {
  const { courseId } = useParams();
  const [tests, setTests] = useState([]);
  const navigate = useNavigate();

const isTestActive = (test) => {
  const now = new Date();
  const start = new Date(new Date(test.start_time).getTime() - 3 * 60 * 60 * 1000);
  const deadline = new Date(new Date(test.deadline).getTime() - 3 * 60 * 60 * 1000);
  return now >= start && now <= deadline;
};


  useEffect(() => {
    const fetchTests = async () => {
      try {
        const res = await axiosInstance.get("/student/tests-by-course/");
        const courseData = res.data.find(c => String(c.id) === String(courseId));

        if (courseData && courseData.tests.length > 0) {
          const testList = courseData.tests
            .filter(t => t.test !== null && t.test !== undefined)
            .map(t => ({
              ...t.test,
              assignment_id: t.id,
              attempt_no: t.attempt_no,
              started_at: t.started_at,
              finished_at: t.finished_at,
              ai_score: t.ai_score,
              manual_score: t.manual_score
            }));

          setTests(testList);
        } else {
          setTests([]);
        }
      } catch (error) {
        console.error("Error loading tests for course", error);
        setTests([]);
      }
    };

    fetchTests();
  }, [courseId]);

  return (
    <div className="test-page-container">
      <h2 style={{ marginBottom: "2rem", color: "#e2d9ff" }}>Available Tests</h2>

      <div className="test-grid">
        {tests.length === 0 ? (
          <p>No available tests for this course.</p>
        ) : (
          tests.map((test) => (
            <div key={test.id} className="test-card">
              <div className="test-header">
                <h3>{test.name}</h3>
                <span>{test.type ? test.type.toUpperCase() : "UNKNOWN"}</span>
              </div>

              <div className="test-details">
                <p><strong>Duration:</strong> {test.duration_minutes} minutes</p>
                <p><strong>Start:</strong> {new Date(test.start_time).toLocaleString("ro-RO", { timeZone: "UTC", hour12: false })}</p>
                <p><strong>Deadline:</strong> {new Date(test.deadline).toLocaleString("ro-RO", { timeZone: "UTC", hour12: false })}</p>
                <p><strong>Target:</strong> Series {test.target_series}, Group {test.target_group}, Subgroup {test.target_subgroup}</p>
              </div>

              <div className="test-options">
                {test.use_proctoring && <span>🔒 Proctoring Enabled</span>}
                {test.has_ai_assistent && <span>🤖 AI Assistant</span>}
                {test.allow_copy_paste && <span>📋 Copy-Paste Allowed</span>}
              </div>

              {test.finished_at && (
                <div className="test-score">
                  <p><strong>AI Score:</strong> {test.ai_score ?? "N/A"}</p>
                  <p><strong>Manual Score:</strong> {test.manual_score ?? "N/A"}</p>
                </div>
              )}

              {!test.finished_at && (
                <button
                onClick={() => navigate(`/tests/start/${test.assignment_id}`)
              }
              style = {{
                opacity:isTestActive(test)?1:0.5,
                cursor:isTestActive(test)?"pointer":"not-allowed",
                marginTop:"1rem",
              }}
              >
                {isTestActive(test) ? "Start Test" : "Unavailable"}
              </button> 
              )}

            </div>
          ))
        )}
      </div>
    </div>
  );
}
