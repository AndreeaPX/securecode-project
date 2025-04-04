import React, { useState } from "react";
import axiosInstance from "../api/axios";
import { useNavigate } from "react-router-dom";
import "./Login.css";
import logo from "../images/logo.jpg";

export default function Login() {
  const [formData, setFormData] = useState({ email: "", password: "" });
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const response = await axiosInstance.post("login/", formData);
      const { access, refresh } = response.data.tokens || {};

      localStorage.setItem("access", access);
      localStorage.setItem("refresh", refresh);
      localStorage.setItem("email", response.data.email);
      localStorage.setItem("first_login", response.data.first_login);

      if (response.data.first_login) {
        navigate("/change-password");
      } else {
        navigate("/"); 
      }
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
