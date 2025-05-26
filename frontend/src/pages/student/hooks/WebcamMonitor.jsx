import React, { useEffect, useRef } from "react";
import axiosInstance from "../../../api/axios";

export default function WebcamMonitor({ assignmentId }) {
  const videoRef = useRef(null);

  useEffect(() => {
  console.log("[WebcamMonitor] Live camera monitor is active");
}, []);
  useEffect(() => {
    let stream;

    const startCamera = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      } catch (err) {
        console.error("Camera access denied:", err);
      }
    };

    const captureAndSend = async () => {
      const canvas = document.createElement("canvas");
      const video = videoRef.current;
      if (!video) return;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext("2d").drawImage(video, 0, 0);
      const dataUrl = canvas.toDataURL("image/jpeg");

      try {
        await axiosInstance.post("/proctoring/live-face-check/", {
          face_image: dataUrl,
          assignment_id: assignmentId
        });
      } catch (err) {
        console.warn("Live face check failed:", err?.response?.data || err.message);
      }
    };

    startCamera();
    const interval = setInterval(captureAndSend, 5000);

    return () => {
      clearInterval(interval);
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [assignmentId]);

  return <video ref={videoRef} style={{ display: "none" }} />;
}
