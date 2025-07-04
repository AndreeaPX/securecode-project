import React, { useState, useEffect } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import axiosInstance from "../../../api/axios";
import useProctoring from "../hooks/useProctoring";
import WebcamMonitor from "../hooks/WebcamMonitor";
import MicrophoneMonitor from "../hooks/MicrophoneMonitor";
import TestFaceCheck from "./StudentTestFaceAuth";
import QuestionRenderer from "../components/questions/QuestionRenderer";
import "../../../styles/TestPage.css";
import useCountdown from "../hooks/useCountdown";
import useUserActivityMonitor from "../hooks/useUserActivityMonitor";


export default function TestPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const [test, setTest] = useState(null);
  const {assignmentId} = useParams();

  const [verified, setVerified] = useState(location.state?.verified || false);
  const [proctoringEnabled, setProctoringEnabled] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const currentQuestion = questions[currentIndex];
  const { showOverlay, reenterFullscreen } = useProctoring({
    enabled: proctoringEnabled,
    navigate,
  });
  const shouldStartCountdown = verified && test?.duration_minutes;
  const [submitting, setSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const shouldMonitor = verified && test?.has_ai_assistent;
  useUserActivityMonitor(shouldMonitor ? assignmentId : null);

  const finished = sessionStorage.getItem(`assignment_${assignmentId}_submitted`) === "true";
  const isTraining = sessionStorage.getItem(`assignment_${assignmentId}_is_training`) === "true";

  const shouldBlock = finished && !isTraining;
  useEffect(() => {
    if (shouldBlock) {
      navigate("/dashboard-student", { replace: true });
    }
  }, [shouldBlock, navigate]);

  if (shouldBlock) {
    return null; 
  }

  const { formatted: timeLeft } = useCountdown(
    shouldStartCountdown ? test.duration_minutes : null,
    async () => {
      alert("Time's up! Submitting your answers...");
      await submitTest();
      if(test?.type !== "training")
      {
        sessionStorage.setItem(`assignment_${assignmentId}_submitted`, "true");
      }
      navigate("/dashboard-student", { replace: true });
    }
  );

  //  Fetch Questions
  useEffect(() => {
  if (!assignmentId) return;

  const fetchTest = async () => {
    try {
      const res = await axiosInstance.get(`/test-assignments/${assignmentId}/`);
      const isTraining = res.data.test?.type === "training";
      sessionStorage.setItem(`assignment_${assignmentId}_is_training`, isTraining ? "true":"false");
      setTest(res.data.test); 
      if (!res.data.started_at) {
      await axiosInstance.patch(`/test-assignments/${assignmentId}/`, {
        started_at: new Date().toISOString(),
      });
    }
    } catch (err) {
      console.error("Failed to load test data", err);
      navigate("/dashboard-student");
    }
  };

  fetchTest();
}, [assignmentId]);

  useEffect(() => {
    if (!assignmentId) return;

    const fetchQuestions = async () => {
      try {
        const res = await axiosInstance.get(`/test-assignments/${assignmentId}/questions/`);
        setQuestions(res.data);
      } catch (err) {
        console.error("Error fetching questions", err);
      }
    };

    fetchQuestions();
  }, [assignmentId]);

  //  Prevent Back
  useEffect(() => {
    window.history.pushState(null, "", window.location.href);
    window.onpopstate = () => {
      window.history.pushState(null, "", window.location.href);
    };
  }, []);

  //Proctoring Kick Check
  useEffect(() => {
    const kicked = sessionStorage.getItem("proctoringKicked");
    if (kicked === "true") {
      alert("Access denied. You violated proctoring conditions.");
      navigate("/dashboard-student");
    }
  }, [navigate]);

  // Redirect if no test
  useEffect(() => {
     if (verified && (!test || !assignmentId))  {
      navigate("/dashboard-student");
    }
  }, [test, assignmentId, navigate]);

  // Start Fullscreen
  const handleFaceCheckSuccess = async () => {
    try {
      if (test?.use_proctoring) {
        const docElm = document.documentElement;
        if (docElm.requestFullscreen) {
          await docElm.requestFullscreen();
        }
        setProctoringEnabled(true);
      }
    } catch (err) {
      console.warn("Fullscreen failed:", err);
    } finally {
      setVerified(true);
      navigate(".", { replace: true, state: { verified: true } });
    }
  };

  //Submit Function
 const submitTest = async () => {
  if (submitting) return;
  setSubmitting(true);
  setIsSubmitted(true);

  const payload = {
    assignment_id: parseInt(assignmentId),
    answers: Object.entries(answers).map(([questionId, answerVal]) => {
      const questionObj = questions.find(
        q => q.id === parseInt(questionId) || q.question?.id === parseInt(questionId)
      );
      const question = questionObj?.question || questionObj;

      const base = { question_id: question.id };

      if (question.type === "open" || question.type === "code") {
        base.answer_text = answerVal;
      } else if (question.type === "single") {
        base.selected_option_ids = [answerVal];
      } else if (question.type === "multiple") {
        base.selected_option_ids = answerVal;
      }

      return base;
    }),
  };

  try {
    const res = await axiosInstance.post("/submit-answers/", payload);
    if (test?.use_proctoring){
      if(document.fullscreenElement){
        await document.exitFullscreen();
      }
      setProctoringEnabled(false);
      if(test?.type !== "training")
      sessionStorage.setItem(`assignment_${assignmentId}_submitted`, "true");
      navigate("/dashboard-student", { replace: true });
    }
    else {
    //alert("Attempt submitted!");
    if(test?.type !== "training")
    sessionStorage.setItem(`assignment_${assignmentId}_submitted`, "true");
    navigate("/dashboard-student", { replace: true });
    }
  } catch (err) {
    if (err.response?.data?.detail) {
          if (test?.use_proctoring){
      navigate("/dashboard-student");}
      else
      alert(`Error: ${err.response.data.detail}`);
    } else {
          if (test?.use_proctoring){
      navigate("/dashboard-student");}
      else
      alert("Something went wrong while submitting. Try again.");
    }
  } finally {
    setSubmitting(false);
  }
};

  //  Logic Next
  const handleNext = async () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      // Final step: navigate or submit
      try{
      if(proctoringEnabled && document.fullscreenElement){
        await document.exitFullscreen();
      }
      setProctoringEnabled(false);
    } catch(err){
      console.warn("Failed to exit fullscreen:", err);
    } 
      console.log("Final answers:", answers);
      await submitTest();
    }
  };

  const updateAnswer = (val) => {
    setAnswers(prev => ({
      ...prev,
      [currentQuestion.id]: val,
    }));
  };

  if (!verified) {
    return <TestFaceCheck onSuccess={handleFaceCheckSuccess} />;
  }




  if (!test) {
  return <p>Loading test...</p>;
  }
console.log("Assignment ID:", assignmentId); 
 return (
  <div className="test-page">
    {!isSubmitted && test?.has_ai_assistent && assignmentId && (
      <WebcamMonitor assignmentId={assignmentId} currentQuestionId={currentQuestion?.id} />
    )}
    
    {!isSubmitted && test?.has_ai_assistent && test?.allow_sound_analysis && assignmentId && (
      <MicrophoneMonitor assignmentId={assignmentId } />
      
    )}
    {/* Test Header */}
    <div className="test-header">
      <h2>{test.name}</h2>
      <div className="test-details">
        <p>Time left: {timeLeft}</p>
        <p>Question {currentIndex + 1} of {questions.length}</p>
      </div>
    </div>

    {/* Question Block */}
    {currentQuestion && (
      <>
        <div className="question-block">
          <strong>{currentQuestion.text}</strong>
          <QuestionRenderer
            question={currentQuestion}
            answer={answers[currentQuestion.id]}
            setAnswer={updateAnswer}
          />
        </div>

        <button
        className="next-button"
          onClick={handleNext}
          disabled={answers[currentQuestion.id] == null}
        >
          {currentIndex === questions.length - 1 ? "Finish" : "Next"}
        </button>
      </>
    )}

    {/* Fullscreen Overlay */}
    {showOverlay && (
      <div className="fullscreen-overlay">
        <p>You exited fullscreen or moved the window. This is your only chance to return.</p>
        <button onClick={reenterFullscreen}>
          Re-enter Fullscreen
        </button>
      </div>
    )}
  </div>
);
}