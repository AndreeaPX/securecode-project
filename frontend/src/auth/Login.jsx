import React, { useState, useEffect } from "react";
import axiosInstance from "../api/axios";
import { useNavigate, useSearchParams } from "react-router-dom";
import "../styles/Login.css";
import logo from "../images/logo.jpg";
import { useAuth } from '../components/AuthProvider'

export default function Login() {
  const [formData, setFormData] = useState({ email: "", password: "" });
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const {setUser} = useAuth();

  useEffect(() => {
    const expired = searchParams.get("expired");
    const alreadyShown = sessionStorage.getItem("alert_shown");
  
    if (expired === "true" && !alreadyShown) {
      alert("Session expired. Please log in again.");
      sessionStorage.setItem("alert_shown", "true");
  
      setTimeout(() => {
        sessionStorage.removeItem("alert_shown");
      }, 2000);
    }
  
    if (localStorage.getItem("accessToken") && localStorage.getItem("user")) {
      navigate("/");
    }
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axiosInstance.post("login/", formData);
      const { access, refresh } = response.data.tokens || {};
      const userData = {
        id:response.data.id,
        email:response.data.email,
        role: response.data.role,
        first_name: response.data.first_name,
        last_name: response.data.last_name,
        first_login: response.data.first_login,
      };
      localStorage.setItem("accessToken", access);
      localStorage.setItem("refreshToken", refresh);
      localStorage.setItem("user", JSON.stringify(userData));
      setUser(userData);

      navigate("/face-login");
    } catch (error) {
      alert("Invalid credentials or something went wrong");
    }
  };

  return (
    <div className="login-container">
      <form className="login-form" onSubmit={handleLogin}>
        <img src={logo} alt="SecureCode" className="login-logo" />
        <h2>SecureCode Login</h2>

        <label>Email</label>
        <input
          type="email"
          name="email"
          placeholder="you@ase.ro"
          onChange={handleChange}
          required
        />

        <label>Password</label>
        <input
          type="password"
          name="password"
          placeholder="••••••••"
          onChange={handleChange}
          required
        />

        <button type="submit">Log In</button>
      </form>
    </div>
  );
}
