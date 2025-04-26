import ProfessorDashboard from "../pages/professor/ProfessorDashBoard";
import StudentDashboard from "../pages/student/StudentDashBoard";
import "../styles/Home.css";
import { useAuth } from "../components/AuthProvider";

export default function Home() {
  const { user } = useAuth();
  const accessToken = localStorage.getItem("accessToken");
  if (!user || !accessToken) return <h2>Loading...</h2>;
  
  if (user.role === "student") return <StudentDashboard />;
  if (user.role === "professor") return <ProfessorDashboard />;
  if (!user || !user.role){
    localStorage.clear();
    window.location.href = "/login?invalid=true";
    return null;
  }
  return <h2>Unauthorized access</h2>;
}
