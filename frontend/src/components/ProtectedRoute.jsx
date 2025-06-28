import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "./AuthProvider";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const accessToken = localStorage.getItem("accessToken");
  const location = useLocation();

  if (loading) return <p>Loading...</p>;

  if (!user || !accessToken) {
    return <Navigate to="/login" replace />;
  }

  if (!user.face_verified && location.pathname !== "/face-login") {
    return <Navigate to="/face-login" replace />;
  }

  return children;
}
