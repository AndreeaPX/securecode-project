import React from "react";
import { Outlet, Link, useLocation } from "react-router-dom";
import "./Layout.css"; 

export default function Layout() {
  const location = useLocation();
  const hideNavbarRoutes = ["/login", "/change-password"];

  return (
    <>
      {!hideNavbarRoutes.includes(location.pathname) && (
        <nav className="nav">
          <ul className="nav-links">
            <li>
              <Link to="/">Home</Link>
            </li>
            <li>
              <Link to="/login">Login</Link>
            </li>
          </ul>
        </nav>
      )}
      <main className="layout-main">
        <Outlet />
      </main>
    </>
  );
}
