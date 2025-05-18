import React, { useEffect, useState } from "react";
import axiosInstance from "../../api/axios";
import { useAuth } from "../../components/AuthProvider";
import "../../styles/StudentDashboard.css";
import {useNavigate} from "react-router-dom";


const bgClasses = ["bg-purple1", "bg-purple2", "bg-purple3", "bg-purple4"];


const getRandomBgClass = () => {
  return bgClasses[Math.floor(Math.random() * bgClasses.length)];
};

export default function StudentDashboard() {
  const { user } = useAuth();
  const [courses, setCourses] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [search, setSearch] = useState("");
  const [year, setYear] = useState("");
  const [semester, setSemester] = useState("");
  const navigate = useNavigate();
  
  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const res = await axiosInstance.get("/dashboard/student-courses/");
        const withStyles = res.data.map(course => ({
          ...course,
          style: getRandomBgClass()
        }));
        setCourses(withStyles);
      } catch (err) {
        console.error("Failed to load student courses:", err);
      }
    };

    fetchCourses();
  }, []);

   useEffect(() => {
    let result = courses;
    if (search) {
      result = result.filter(c => c.name.toLowerCase().includes(search.toLowerCase()));
    }
    if (year) {
      result = result.filter(c => String(c.year) === year);
    }
    if (semester) {
      result = result.filter(c => String(c.semester) === semester);
    }
    setFiltered(result);
  }, [search, year, semester, courses]);

  return (
    <div className="student-dashboard">
<div className="student-dashboard-wrapper">
  <h2 className="student-dashboard-title">My Courses</h2>
  <div className="course-grid">
    {courses.map((course) => (
      <div key={course.id} className={`course-card ${course.style}`}
      onClick={() => navigate(`/student/tests/${course.id}`)}
      style={{cursor:"pointer"}}>
        <div className="course-name">{course.name}</div>
        <div className="course-details">Year {course.year} – Semester {course.semester}</div>
      </div>
    ))}
  </div>
</div>

    </div>
  );
}
