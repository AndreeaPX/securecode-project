import React, { useState } from "react";
import axiosInstance from "../api/axios";
import { useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { useAuth } from "../components/AuthProvider";

export default function ChangePassword() {
  const [passwords, setPasswords] = useState({
    new_password: "",
    confirm_password: "",
  });
  const navigate = useNavigate();
  const { setUser } = useAuth();

  useEffect(() => {
    const firstLogin = localStorage.getItem("first_login");
    if(firstLogin == "false"){
      navigate("/");
    }
  }, []);

  const handleChange = (e) => {
    setPasswords({ ...passwords, [e.target.name]: e.target.value });
  };


  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axiosInstance.post(
        "change-password/",
        {
          new_password: passwords.new_password,
          confirm_password: passwords.confirm_password,
        },
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("accessToken")}`,
          },
        }
      );

      alert("Password changed successfully! Pleasy try to log in again!");
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("user");
      setUser(null);
      navigate("/login", { replace: true });

    } catch (err) {
      if (err.response && err.response.data && err.response.data.error) {
        const errors = err.response.data.error;
        const message = Array.isArray(errors) ? errors.join("\n") : errors;
        alert(message);
      } else {
        alert("Error changing password");
      }
    }
  };

  
  return (
    <div className="login-container">
      <form className="login-form" onSubmit={handleSubmit}>
        <h2>Set Your New Password</h2>

        <label>New Password:</label>
        <input
          type="password"
          name="new_password"
          onChange={handleChange}
          required
        />
        <br />
        <label>Confirm Password:</label>
        <input
          type="password"
          name="confirm_password"
          onChange={handleChange}
          required
        />
        <br />
        <button type="submit">Change Password</button>
      </form>
    </div>
  );

}
