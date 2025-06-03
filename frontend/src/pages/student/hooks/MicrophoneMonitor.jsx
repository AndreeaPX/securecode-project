import React, { useEffect, useRef } from "react";
import axiosInstance from "../../../api/axios";

export default function MicMonitor({ assignmentId }) {
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const intervalRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    console.log("[MicMonitor] Starting microphone monitor...");
    let isUnmounted = false;

    const initMic = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;

        mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: "audio/webm" });

        mediaRecorderRef.current.ondataavailable = (e) => {
          if (e.data.size > 0) chunksRef.current.push(e.data);
        };

        mediaRecorderRef.current.onstop = async () => {
          const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
          chunksRef.current = [];

          const formData = new FormData();
          formData.append("assignment_id", assignmentId);
          formData.append("audio_file", audioBlob, "chunk.webm");

          try {
            await axiosInstance.post("/proctoring/live-audio-check/", formData, {
              headers: { "Content-Type": "multipart/form-data" },
            });
            console.log("[MicMonitor] Audio chunk sent");
          } catch (err) {
            console.warn("Audio check failed:", err?.response?.data || err.message);
          }

          // Reîncepe înregistrarea doar dacă încă suntem activi
          setTimeout(() => {
            if(!isUnmounted && streamRef.current && streamRef.current.active){
              mediaRecorderRef.current.start();
            }
          })
        };

        //mediaRecorderRef.current.start();

        intervalRef.current = setInterval(() => {
          if (mediaRecorderRef.current?.state === "recording") {
            mediaRecorderRef.current.stop(); // va declanșa onstop
          }
        }, 3000);

      } catch (err) {
        console.error("Microphone access denied:", err);
      }
    };

    const cleanupMic = () => {
      console.log("[MicMonitor] Cleaning up microphone access");
      isUnmounted = true;
      clearInterval(intervalRef.current);
      if (mediaRecorderRef.current?.state === "recording") {
        mediaRecorderRef.current.stop();
      }
      streamRef.current?.getTracks().forEach((track) => track.stop());
    };

    initMic();


    return () => {
      cleanupMic();
    };

  }, [assignmentId]);


  return null;
}
