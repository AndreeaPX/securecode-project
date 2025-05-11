import React, { useState, useEffect } from "react";
import axios from "axios";
import axiosInstance from "../../api/axios";
import { useAuth } from "../../components/AuthProvider";
import "../../styles/Questions.css";
import { useNavigate } from "react-router-dom";

export default function Questions() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [questions, setQuestions] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState({
    course: "",
    type: "",
    date: "",
  });

  // === Refactor pentru refresh control ===
  let isRefreshingToken = false;
  let refreshPromise = null;

  const isTokenExpiringSoon = () => {
    const token = localStorage.getItem("accessToken");
    if (!token) return true;
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      const now = Math.floor(Date.now() / 1000);
      return payload.exp - now < 60;
    } catch {
      return true;
    }
  };

  const refreshAccessToken = async () => {
    if (isRefreshingToken && refreshPromise) {
      console.log(" Waiting for ongoing refresh...");
      return refreshPromise;
    }

    const refreshToken = localStorage.getItem("refreshToken");
    if (!refreshToken) throw new Error("Refresh token missing");

    isRefreshingToken = true;
    refreshPromise = axios
      .post(`${import.meta.env.VITE_API_URL}token/refresh/`, { refresh: refreshToken }, { withCredentials: true })
      .then((res) => {
        const newAccessToken = res.data.access;
        localStorage.setItem("accessToken", newAccessToken);
        console.log("Token refreshed");
      })
      .catch((err) => {
        console.error(" Token refresh failed:", err);
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        window.location.href = "/login?expired=true";
        throw err;
      })
      .finally(() => {
        isRefreshingToken = false;
        refreshPromise = null;
      });

    return refreshPromise;
  };

  useEffect(() => {
    if (!user) return;

    const init = async () => {
      try {
        if (isTokenExpiringSoon()) {
          console.log("Token expiring – refreshing...");
          await refreshAccessToken();
        }
        await fetchCoursesAndQuestions();
      } catch (err) {
        console.error("Token validation or fetch failed:", err);
        window.location.href = "/login?expired=true";
      }
    };

    init();
  }, [user]);

  const fetchCoursesAndQuestions = async () => {
    try {
      const coursesRes = await axiosInstance.get("/courses/");
      setCourses(coursesRes.data);
      await fetchQuestions();
    } catch (err) {
      console.error("Failed to load courses or questions:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchQuestions = async () => {
    try {
      const params = {};
      if (searchTerm) params.search = searchTerm;
      if (filters.course) params.course = filters.course;
      if (filters.type) params.type = filters.type;
      if (filters.date) params.created_at__date = filters.date;

      const res = await axiosInstance.get("/questions/", { params });
      setQuestions(res.data);
    } catch (err) {
      console.error("Failed to load questions:", err);
    }
  };

  const handleSearchChange = (e) => setSearchTerm(e.target.value);

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters({ ...filters, [name]: value });
  };

  const handleResetFilters = () => {
    setSearchTerm("");
    setFilters({ course: "", type: "", date: "" });
    fetchQuestions();
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchQuestions();
  };

  const handleDelete = async (id) => {
    try {
      await axiosInstance.delete(`/questions/${id}/`);
      fetchQuestions();
    } catch (err) {
      console.error("Failed to delete question:", err);
    }
  };

  if (loading) return <p>Loading questions...</p>;

  return (
    <div className="questions-page">
      <form onSubmit={handleSearchSubmit} className="search-filters-container">
        <input
          type="text"
          placeholder="Search questions..."
          value={searchTerm}
          onChange={handleSearchChange}
        />
        <select name="course" value={filters.course} onChange={handleFilterChange}>
          <option value="">All Courses</option>
          {courses.map((course) => (
            <option key={course.id} value={course.id}>
              {course.name}
            </option>
          ))}
        </select>
        <select name="type" value={filters.type} onChange={handleFilterChange}>
          <option value="">All Types</option>
          <option value="single">Single Choice</option>
          <option value="multiple">Multiple Choice</option>
          <option value="open">Open Answer</option>
          <option value="code">Code Response</option>
        </select>
        <input
          type="date"
          name="date"
          value={filters.date}
          onChange={handleFilterChange}
        />
        <button type="submit">Apply Filters</button>
        <button type="button" onClick={handleResetFilters}>
          Reset Filters
        </button>
      </form>

      <div className="questions-table-container">
        <table className="questions-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Question</th>
              <th>Type</th>
              <th>Points</th>
              <th>Options</th>
            </tr>
          </thead>
          <tbody>
            {questions.map((q, index) => (
              <tr key={q.id}>
                <td>{index + 1}</td>
                <td>{q.text}</td>
                <td>{q.type}</td>
                <td>{q.points}</td>
                <td>
                  {q.created_by === user.id ? (
                    <>
                      <button onClick={()=>navigate(`/questions/view/${q.id}`)}>Open</button>
                      <button onClick={() => navigate(`/questions/edit/${q.id}`)}>Edit</button>
                      <button onClick={() => handleDelete(q.id)}>Delete</button>
                    </>
                  ) : (
                    <button onClick={()=>navigate(`/questions/view/${q.id}`)}>Open</button>
                  )
                }
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <button
        className="floating-create-button"
        onClick={() => navigate('/questions/create')}
      >
        Create
      </button>
    </div>
  );
}
