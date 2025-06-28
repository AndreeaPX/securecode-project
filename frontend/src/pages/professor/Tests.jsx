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
  const [searchTerm, setSearchTerm] = useState("");
  const [filters,setFilters] = useState({
    course:"",
    type:"",
    start_time :"",
  });

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

  const fetchTests = async () =>{
    try {
      const params = {};
      if(searchTerm) params.search = searchTerm;
      if(filters.course) params.course = filters.course;
      if(filters.type) params.type = filters.type;
      if(filters.start_time) params.start_time__date = filters.start_time;
      console.log(filters.start_time)
      console.log(params.start_time__date)

      const res = await axiosInstance.get("/tests/", {params});
      console.log("Fetched tests with filters:", res.data);
      setTests(res.data);
    } catch (err){
      console.error("Failed to load tests:", err);
    }
  };

  const handleSearchChange = (e) => setSearchTerm(e.target.value);

  const handleFilterChange = (e) => {
    const {name, value} = e.target;
    setFilters({...filters, [name]:value});
  };

  const handleResetFilters = () => {
    setSearchTerm("");
    setFilters({course:"", type:"", start_time:""});
    fetchTests();
  }

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchTests();
  }
  

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this test draft?")) return;
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

      <form onSubmit={handleSearchSubmit} className="search-filters-container">
        <input
          type = "text"
          placeholder="Search tests..."
          value={searchTerm}
          onChange={handleSearchChange}
        />
        <select name = "course" value={filters.course} onChange={handleFilterChange}>
          <option value="">All Courses</option>
          {courses.map((course) => (
            <option key={course.id} value={course.id}>
              {course.name}
            </option>
          ))}
        </select>
        <select name="type" value={filters.type} onChange={handleFilterChange}>
          <option value="">All Types</option>
          <option value="exam">Exam Test</option>
          <option value="seminar">Seminar Test</option>
          <option value="training">Training Test</option>
        </select>
        <input
          type="date"
          name = "start_time"
          value = {filters.start_time}
          onChange={handleFilterChange}
        />
        <button type="submit">Apply Filters</button>
        <button type="button" onClick={handleResetFilters}>Reset Filters</button>
      </form>

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
                  {test.is_submitted ? (
                    <button onClick={() => navigate(`/tests/view/${test.id}`)}>Open</button>
                  ) : (
                    <>
                      <button onClick={() => navigate(`/tests/edit/${test.id}`)}>Edit</button>
                      <button onClick={() => handleDelete(test.id)}>Delete</button>
                    </>
                  )}
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
