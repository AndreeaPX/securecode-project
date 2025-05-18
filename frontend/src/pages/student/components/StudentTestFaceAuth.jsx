import React, { useEffect, useRef, useState } from "react";
import axiosInstance from "../../../api/axios";
import { useAuth } from "../../../components/AuthProvider";
import "../../../styles/StudentTestFaceAuth.css";

export default function StudentTestFaceAuth({ onSuccess }) {
  const { user } = useAuth();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) return;

    let activeStream = null;

    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((stream) => {
        activeStream = stream;
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      })
      .catch(() => {
        setMessage("Could not access camera. Please allow permissions.");
      });

    return () => {
      stopCamera();
    };
  }, [user]);

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.stop();
        track.enabled = false;
      });
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.srcObject = null;
      videoRef.current.load(); 
    }
  };

  const handleCaptureAndVerify = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const ctx = canvasRef.current.getContext("2d");
    ctx.drawImage(videoRef.current, 0, 0, 720, 400);
    const faceData = canvasRef.current.toDataURL("image/jpeg");

    setLoading(true);
    setMessage("");

    try {
      const res = await axiosInstance.post("/face-login/", {
        face_image: faceData,
      });

      if (res.data.success) {
        setMessage("Face verified successfully.");
        stopCamera();

        setTimeout(() => {
          if (onSuccess) onSuccess();
        }, 100);
      } else {
        setMessage("Face verification failed.");
      }
    } catch (err) {
      console.error("Face login error:", err.response?.data || err.message);
      setMessage("Server error during face verification.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="face-check-wrapper">
      <div className="face-check-card">
        <h2>Confirm your identity before starting the test</h2>
        <div className="face-check-camera">
          <video ref={videoRef} autoPlay width={720} height={400} />
          <canvas ref={canvasRef} width={720} height={400} style={{ display: "none" }} />
        </div>
        <button onClick={handleCaptureAndVerify} disabled={loading}>
          {loading ? "Verifying..." : "Capture & Continue"}
        </button>
        <p className="face-check-message">{message}</p>
      </div>
    </div>
  );
}
