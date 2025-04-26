import React, { useEffect, useState } from "react";
import { useAuth } from "../components/AuthProvider";
import { Link } from "react-router-dom";
import axiosInstance from "../api/axios";
import "../styles/Settings.css";

export default function Settings() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);

  if (!user) return <p>You are not logged in.</p>;
  const isProfessor = user.role === "professor";
  const isStudent = user.role === "student";
  
  useEffect(() => {
    if (!user) return;

    const pathBackend = isProfessor ? "/settings/professor/" : isStudent ? "/settings/student/" : null;

    if (!pathBackend) return;

    axiosInstance
      .get(pathBackend).then((res) => {
        setProfile(res.data);
      })
      .catch((err) => {
        console.error("Failed to load settings:", err);
      });
  }, [user]);

  if (!profile) return <p>Loadding profile...</p>;

  return (
    <div className="settings-page">
      <div className="settings-card">
        <h2>Account Details</h2>

        <div className="info-group">
          <p><strong>Full Name:</strong> {user.first_name} {user.last_name}</p>
          <p><strong>Email:</strong> {user.email}</p>
          <p><strong>Role:</strong> {user.role}</p>
          <p><strong>Start Date:</strong> {profile.start_date}</p>
        </div>

        {isProfessor && profile && (
          <div className="info-group">
            <h3>Professor Details</h3>
            <p><strong>Specialization:</strong> {profile.specialization.name}</p>
            <p><strong>Teaches Lecture:</strong> {profile.teaches_lecture ? "Yes" : "No"}</p>
            <p><strong>Teaches Seminar:</strong> {profile.teaches_seminar ? "Yes" : "No"}</p>
            <p><strong>Courses:</strong> {profile.courses.map(c => c.name).join(", ")}</p>
          </div>
        )}

        {isStudent && profile && (
          <div className="info-group">
            <h3>Student Details</h3>
            <p><strong>Specialization:</strong> {profile.specialization.name}</p>
            <p><strong>Degree:</strong> {profile.group_type === "b" ? "Bachelor" : (profile.group_type === "m") ? "Master" : "Doctorate"}</p>
            <p><strong>Group:</strong> {profile.group}</p>
            <p><strong>Series:</strong> {profile.series}</p>
            <p><strong>Subgroup:</strong> {profile.subgroup}</p>
            <p><strong>Year:</strong> {profile.year}</p>
            <p><strong>Courses:</strong> {profile.courses.map(c => c.name).join(", ")}</p>
          </div>
        )}

        <Link className="change-password-button" to="/change-password">
          Change Password
        </Link>
      </div>
    </div>
  );
}
