import React, { useEffect, useRef, useState } from "react";
import axiosInstance from "../api/axios";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../components/AuthProvider";
import "../styles/FaceLogin.css";

export default function FaceLogin() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const navigate = useNavigate();
  const { user, setUser, logout } = useAuth();
  const [message, setMessage] = useState("");

  useEffect(() => {

    let activeStream = null;

    if (!user) {
      navigate("/login");
      return;
    }

    navigator.mediaDevices.getUserMedia({ video: true })
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
  }, [user, navigate]);

  const stopCamera = () => {
    if(streamRef.current){
        streamRef.current.getTracks().forEach((track)=>{
            track.stop();
            track.enabled = false;
        });

        if(videoRef.current){
            videoRef.current.pause();
            videoRef.current.srcObject = null;
            videoRef.current.load();
        }
        streamRef.current = null;
    }
  };  


  const handleCaptureAndVerify = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const ctx = canvasRef.current.getContext("2d");
    ctx.drawImage(videoRef.current, 0, 0, 720, 400);
    const faceData = canvasRef.current.toDataURL("image/jpeg");

    try {
      const res = await axiosInstance.post("face-login/", {
        email: user.email,
        face_image: faceData,
      });
      if (res.data.success) {
        setMessage("Face authenticated.");
        stopCamera();
        videoRef.current.srcObject = null;
        window.location.href = user.first_login ? "/change-password" : "/";
      } else {
        setMessage("Face authentication failed. Please try again.");
        stopCamera();
        logout(true);
      }
    } catch (err) {
      console.error("Face login error:", err.response?.data || err.message);
        const status = err?.response?.status;
        if ([401, 403, 429].includes(status)) {
          setMessage("Authentication error: " + (err.response?.data?.error || "Access denied"));
          logout(true);
          return;
        }
        setMessage("Server error during face verification.");
      }
  };

  return (
    <div className="face-login-wrapper">
      <div className="face-login-card">
        <h2>Face Recognition Login</h2>
        <div className="face-login-camera">
          <video ref={videoRef} autoPlay width={720} height={400} />
          <canvas ref={canvasRef} width={720} height={400} />
        </div>
        <button className="face-login-button" onClick={handleCaptureAndVerify}>
          Capture & Login
        </button>
        <p className="face-login-message">{message}</p>
      </div>
    </div>
  );
}
