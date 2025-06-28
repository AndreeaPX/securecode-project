import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Layout from "./layouts/Layout";
import Login from "./auth/Login";
import ChangePassword from "./auth/ChangePassword";
import FaceLogin from "./auth/FaceLogin";
import Settings from "./pages/Settings";
import Questions from "./pages/professor/Questions";
import CreateQuestion from './pages/professor/question_components/CreateQuestion';
import QuestionView from './pages/professor/question_components/QuestionView';
import Tests from "./pages/professor/Tests";
import CreateTest from "./pages/professor/test_components/CreateTest";
import StudentDashboard from "./pages/student/StudentDashBoard";
import StudentCourseTest from "./pages/student/components/StudentCourseTest";
import TestPage from "./pages/student/components/TestPage";
import AttentionLiveView from "./pages/professor/components/AttentionLiveView";
import Marks from "./pages/professor/marks/Marks";
import MarksAssignments from "./pages/professor/marks/MarksAssignments";
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
          <Route path="/settings" element={<Settings />} />

          <Route path="/questions" element={<Questions />} />
          <Route path="/questions/create" element={<CreateQuestion />} />
          <Route path="/questions/edit/:questionId" element={<CreateQuestion/>}/>
          <Route path="/questions/view/:questionId" element={<QuestionView readonly={true} />} />
          <Route path="/tests" element={<Tests />} />
          <Route path="/tests/create" element={<CreateTest editMode={false} viewMode={false}/>} />
          <Route path="/tests/edit/:testId" element={<CreateTest editMode={true} viewMode={false}/>} />
          <Route path="/marks" element={<Marks />} />
          <Route path="/marks/:testId" element={<MarksAssignments />} />
          <Route path="/tests/view/:testId" element={<CreateTest editMode={false} viewMode={true} />} />
          <Route path="/dashboard-student" element={<StudentDashboard />} />
          <Route path="/student/courses/:courseId/tests" element={<StudentCourseTest />} />
          <Route path="/attention/live" element={<AttentionLiveView />} />
        </Route>

        <Route path="/tests/start/:assignmentId" element={<ProtectedRoute><TestPage /></ProtectedRoute>} />

        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/change-password" element={<ChangePassword />} />
        <Route path="/face-login" element={<FaceLogin />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
