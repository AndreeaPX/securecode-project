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
    const fetchProfile = async () => {
      if (!user) return;

      const pathBackend = isProfessor
        ? "/settings/professor/"
        : isStudent
        ? "/settings/student/"
        : null;

      if (!pathBackend) return;

      try {
        const res = await axiosInstance.get(pathBackend);
        setProfile(res.data);
      } catch (err) {
        console.error("Failed to load settings:", err);
      }
    };

    fetchProfile();
  }, [user]);

  if (!profile) return <p>Loading profile...</p>;

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
            <p><strong>Specialization:</strong> {profile.specialization?.name || "N/A"}</p>
            <p><strong>Teaches Lecture:</strong> {profile.teaches_lecture ? "Yes" : "No"}</p>
            <p><strong>Teaches Seminar:</strong> {profile.teaches_seminar ? "Yes" : "No"}</p>
            <p><strong>Courses:</strong> {profile.courses?.map(c => c.name).join(", ") || "None"}</p>

            {profile.teaches_seminar && profile.seminar_groups?.length > 0 && (
              <>
                <h3>Seminar Groups</h3>
                {profile.seminar_groups.map((group, idx) => (
                  <div key={idx} style={{ marginBottom: "0.5rem" }}>
                    <p><strong>Group Number:</strong> {group.number}</p>
                    <p><strong>Series:</strong> {group.series.name}</p>
                    <p><strong>Year:</strong> {group.series.year}</p>
                    <p><strong>Degree:</strong> {
                      group.series.group_type === "b" ? "Bachelor"
                      : group.series.group_type === "m" ? "Master"
                      : group.series.group_type === "d" ? "Doctorate"
                      : "Unknown"
                    }</p>
                    <p><strong>Specialization:</strong> {group.series.specialization.name}</p>
                    <hr />
                  </div>
                ))}
              </>
            )}

            {profile.teaches_lecture && profile.lecture_series?.length > 0 && (
              <>
                <h4>Lecture Series</h4>
                {profile.lecture_series.map((series, idx) => (
                  <div key={idx} style={{ marginBottom: "0.5rem" }}>
                    <p><strong>Series Name:</strong> {series.name}</p>
                    <p><strong>Year:</strong> {series.year}</p>
                    <p><strong>Degree:</strong> {
                      series.group_type === "b" ? "Bachelor"
                      : series.group_type === "m" ? "Master"
                      : series.group_type === "d" ? "Doctorate"
                      : "Unknown"
                    }</p>
                    <p><strong>Specialization:</strong> {series.specialization.name}</p>
                    <hr />
                  </div>
                ))}
              </>
            )}
          </div>
        )}


        {isStudent && profile && (
          <div className="info-group">
            <h3>Student Details</h3>

            <p><strong>Group Number:</strong> {profile.group?.number || "N/A"}</p>

            {profile.group?.series ? (
              <>
                <p><strong>Series:</strong> {profile.group.series.name}</p>
                <p><strong>Series Year:</strong> {profile.group.series.year}</p>
                <p><strong>Degree:</strong> {
                  profile.group.series.group_type === "b" ? "Bachelor"
                  : profile.group.series.group_type === "m" ? "Master"
                  : profile.group.series.group_type === "d" ? "Doctorate"
                  : "Unknown"
                }</p>
                <p><strong>Specialization:</strong> {profile.group.series.specialization?.name || "N/A"}</p>
              </>
            ) : (
              <p><strong>Series:</strong> Not assigned</p>
            )}

            <p><strong>Subgroup:</strong> {profile.subgroup}</p>
            <p><strong>Year:</strong> {profile.year}</p>
            <p><strong>Courses:</strong> {profile.courses?.map(c => c.name).join(", ") || "None"}</p>
          </div>
        )}

        <Link className="change-password-button" to="/change-password">
          Change Password
        </Link>
      </div>
    </div>
  );
}
