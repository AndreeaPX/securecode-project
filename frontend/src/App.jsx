import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Layout from "./layouts/Layout";
import Login from "./auth/Login";
import ChangePassword from "./auth/ChangePassword";
import Settings from "./pages/Settings";
import { useEffect } from "react";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  useEffect(() => {
    fetch("https://localhost:8000/csrf/", {
      credentials: "include",
    });
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        {/* Protected Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Home />} />
          <Route path="settings" element={<Settings />} />
          {/*pagini protejate de adaugat */}
        </Route>

        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/change-password" element={<ChangePassword />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
