import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axiosInstance from "../../../api/axios";
import "../../../styles/Questions.css";

export default function MarksAssignments() {
  const { testId } = useParams();
  const navigate = useNavigate();
  const [assignments, setAssignments] = useState([]);
  const [testName, setTestName] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAssignments = async () => {
      try {
        const [testRes, asgRes] = await Promise.all([
          axiosInstance.get(`/tests/${testId}/`),
          axiosInstance.get(`/marks/${testId}/`)
        ]);
        setTestName(testRes.data.name);
        setAssignments(asgRes.data);
      } catch (err) {
        console.error("Failed to load assignments:", err);
      } finally {
        setLoading(false);
      }
    };
    loadAssignments();
  }, [testId]);

  if (loading) return <p>Loading assignments...</p>;

  return (
    <div className="questions-page">
      <h2>{testName} – Student Assignments</h2>

      <div className="questions-table-container">
      <table className="questions-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Email</th>
            <th>Attempt</th>
            <th>Started</th>
            <th>Finished</th>
            <th>Status</th>
            <th>Score</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {assignments.map((a, idx) => (
            <tr key={a.id}>
              <td>{idx + 1}</td>
              <td className="email-cell" title={a.student_email}>
                {a.student_email}
              </td>
              <td>{a.attempt_no}</td>
              <td>{a.started_at?.slice(11, 16) || "-"}</td>
              <td>{a.finished_at?.slice(11, 16) || "-"}</td>
              <td>{a.status}</td>
              <td>{a.auto_score ?? "-"}</td>
              <td>
                <button
                  disabled={a.status !== "finalized"}
                  onClick={() => navigate(`/assignments/${a.id}/review`)}
                >
                  Open
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
          </div>
      <button onClick={() => navigate("/marks")} style={{ marginTop: "1rem" }}>
        ⟵ Back to Test List
      </button>
    </div>
  );
}
