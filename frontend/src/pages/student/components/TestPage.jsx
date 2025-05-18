import React, { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import useProctoring from "../hooks/useProctoring";
import TestFaceCheck from "./StudentTestFaceAuth";

export default function TestPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const test = location.state?.test;

  const [verified, setVerified] = useState(location.state?.verified || false);
  const [proctoringEnabled, setProctoringEnabled] = useState(false);

  const { showOverlay, reenterFullscreen } = useProctoring({
    enabled: proctoringEnabled,
    navigate,
  });

  // Block re-entry if user was kicked
  useEffect(() => {
    const kicked = sessionStorage.getItem("proctoringKicked");
    if (kicked === "true") {
      alert("Access denied. You violated proctoring conditions.");
      navigate("/dashboard-student");
    }
  }, [navigate]);

  // Redirect if test data is missing
  useEffect(() => {
    if (!test || !location.state) {
      navigate("/dashboard-student");
    }
  }, [test, location.state, navigate]);

  // Trigger fullscreen & proctoring only if required
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
    }
  };

  if (!verified) {
    return <TestFaceCheck onSuccess={handleFaceCheckSuccess} />;
  }

  return (
    <div className="test-page" style={{ padding: "1rem" }}>
      <h2>{test.name}</h2>
      <p>Duration: {test.duration_minutes} minutes</p>

      <textarea
        rows="5"
        style={{ width: "100%", marginTop: "1rem" }}
        placeholder="Try to paste here. It won't work."
      />

      {showOverlay && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0,0,0,0.95)",
            color: "#fff",
            zIndex: 9999,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            textAlign: "center",
            padding: "2rem",
          }}
        >
          <p>You exited fullscreen or moved the window. This is your only chance to return.</p>
          <button
            style={{
              padding: "1rem",
              marginTop: "1rem",
              fontSize: "1.2rem",
            }}
            onClick={reenterFullscreen}
          >
            Re-enter Fullscreen
          </button>
        </div>
      )}
    </div>
  );
}
