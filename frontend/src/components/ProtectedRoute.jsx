import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthProvider";

export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const accessToken = localStorage.getItem("accessToken");

  if (loading) return <p>Loading...</p>;

  if (!user || !accessToken) {
    return <Navigate to="/login" replace />;
  }

  return children;
}
