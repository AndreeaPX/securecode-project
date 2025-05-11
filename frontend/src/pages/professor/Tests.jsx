import React, { useState, useEffect } from "react";
import axiosInstance from "../../api/axios";
import { useAuth } from "../../components/AuthProvider";
import { useNavigate } from "react-router-dom";
import "../../styles/Questions.css"; 

export default function Tests() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tests, setTests] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    const loadData = async () => {
      try {
        const [coursesRes, testsRes] = await Promise.all([
          axiosInstance.get("/courses/"),
          axiosInstance.get("/tests/")
        ]);
        setCourses(coursesRes.data);
        setTests(testsRes.data);
      } catch (err) {
        console.error("Error loading tests:", err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [user]);

  const getCourseName = (courseId) => {
    const course = courses.find((c) => c.id === courseId);
    return course ? course.name : "Unknown";
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this test?")) return;
    try {
      await axiosInstance.delete(`/tests/${id}/`);
      setTests((prev) => prev.filter((t) => t.id !== id));
    } catch (err) {
      console.error("Failed to delete test:", err);
    }
  };

  if (loading) return <p>Loading tests...</p>;

  return (
    <div className="questions-page">
      <h2>Your Created Tests</h2>
      <div className="questions-table-container">
        <table className="questions-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Course</th>
              <th>Type</th>
              <th>Start</th>
              <th>Deadline</th>
              <th>Duration</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tests.map((test, index) => (
              <tr key={test.id}>
                <td>{index + 1}</td>
                <td>{test.name}</td>
                <td>{getCourseName(test.course)}</td>
                <td>{test.type}</td>
                <td>{test.start_time ? test.start_time.split("T")[0] : "-"}</td>
                <td>{test.deadline ? test.deadline.split("T")[0] : "-"}</td>
                <td>{test.duration_minutes} min</td>
                <td>
                  <button onClick={() => navigate(`/tests/edit/${test.id}`)}>Edit</button>
                  <button onClick={() => handleDelete(test.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <button
        className="floating-create-button"
        onClick={() => navigate("/tests/create")}
      >
        Create Test
      </button>
    </div>
  );
}
