import React from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../components/AuthProvider";
import "../styles/Layout.css";
import { NavLink } from "react-router-dom";
import logo from "../images/logo.jpg";

export default function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const hideNavbarRoutes = ["/login", "/change-password"];

  const professorLinks = [
    { to: "/", label: "Dashboard" },
    { to: "/questions", label: "Questions" },
    { to: "/tests", label: "Tests" },
    { to: "/marks", label: "Marks" },
    { to: "/settings", label: "Settings" },
  ];

  const studentLinks = [
    { to: "/", label: "My Tests" },
    { to: "/results", label: "Results" },
    { to: "/settings", label: "Settings" },
  ];

  const links = user?.role === "student" ? studentLinks : professorLinks;

  return (
    <>
      {!hideNavbarRoutes.includes(location.pathname) && (
        <nav className="nav">
          <div className="nav-logo">
            <img src={logo} alt="SecureCode logo"/>
            <span>SecureCode</span>
          </div>

          <ul className="nav-links">
          {links.map((link) => (
          <li key={link.to}>
          <NavLink 
            to={link.to}
            className={({isActive}) => (isActive ? "active":"")}>
              {link.label}
            </NavLink>
          </li>
          ))}
        </ul>

          <div className="nav-user">
            <span>{user?.email} ({user?.role})</span>
            <button onClick={() => logout(true)}>Logout</button>
          </div>
        </nav>        
      )}
      <main className="layout-main">
        <Outlet />
      </main>
    </>
  );
}
