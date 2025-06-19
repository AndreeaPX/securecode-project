import Welcome from "../professor/components/Welcome";
import StudentProgress from "../professor/components/StudentProgress";
import GradingProgress from "../professor/components/GradingProgress";
import PieChartComponent from "../professor/components/PieChartComponent";
import BarChartComponent from "../professor/components/BarChartComponent";
import BiometricSummaryCard from "./components/BiometricSummaryCard";
import AttentionSessionCard from "./components/AttentionSessionCard";
import "./ProfessorDashBoard.css";

export default function ProfessorDashboard() {
    return (
      <div className="dashboard-page">
        <Welcome />
  
        <div className="dashboard-widgets">
          <div className="widget">
            <h3 className="card-title">Student Progress</h3>
            <StudentProgress />
          </div>
  
          <div className="widget">
            <h3 className="card-title">Grading Progress</h3>
            <GradingProgress />
          </div>
        </div>
  
        <hr className="section-divider" ></hr>
  
        <div className="dashboard-stats-section">
          <h3 className="card-title">Test Statistics Overview</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <PieChartComponent />
            </div>
            <div className="stat-card">
              <BarChartComponent />
            </div>
            <div className="stat-card">
              <BiometricSummaryCard />
            </div>
          </div>
          <div className="stat-card">
          <AttentionSessionCard />
        </div>
        </div>
      </div>
    );
  }