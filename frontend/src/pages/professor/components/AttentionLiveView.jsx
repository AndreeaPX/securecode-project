import { useEffect, useRef, useState } from "react";
import axios from "../../../api/axios";
import { useNavigate, useSearchParams } from "react-router-dom";
import "./AttentionLiveView.css";

export default function AttentionLiveView() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);
  const feedbackIntervalRef = useRef(null); // 🆕 ref for feedback polling
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session");
  const navigate = useNavigate();
  const [ending, setEnding] = useState(false);
  const [feedbackLog, setFeedbackLog] = useState([]);

  useEffect(() => {
    let streamRef = null;
    navigator.mediaDevices.getUserMedia({ video: true, audio: false })
      .then(stream => {
        streamRef = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      })
      .catch(err => alert("Camera error: " + err.message));

    // frame capture every 5 s (existing behaviour)
    intervalRef.current = setInterval(() => captureAndSendFrame(), 5000);
    // feedback polling every 30 s (new)
    feedbackIntervalRef.current = setInterval(() => fetchFeedbackTips(), 30000);

    return () => {
      clearInterval(intervalRef.current);
      clearInterval(feedbackIntervalRef.current);
      if (streamRef) {
        streamRef.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const captureAndSendFrame = async () => {
    const video = videoRef.current;
    if (!video || video.videoWidth === 0) return;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);

    const frame = canvas.toDataURL("image/jpeg");
    const { data } = await axios.post("attention/check/", {
      frame,
      session_id: sessionId,
    });

    const ctx = canvasRef.current.getContext("2d");
    canvasRef.current.width = video.videoWidth;
    canvasRef.current.height = video.videoHeight;
    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);

    data.faces.forEach(({ x, y, w, h, attentive }) => {
      ctx.strokeStyle = attentive ? "lime" : "red";
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, w, h);
      ctx.fillStyle = attentive ? "lime" : "red";
      ctx.font = "16px Arial";
      ctx.fillText(attentive ? "🙂 paying" : "🙄 distracted", x, y - 10);
    });
  };

  // 🆕 fetch feedback tips every 30 s
const fetchFeedbackTips = async () => {
  try {
    const { data } = await axios.post("attention/feedback/", {
      session_id: sessionId,
    });
    const timestamp = new Date().toLocaleTimeString();

  if (typeof data.tip === "string" && data.tip.trim()) {
    const formatted = `📊 Attention: ${data.attention_avg}% → ${data.tip.trim()}`;
    setFeedbackLog(prev => [...prev, { time: timestamp, tips: [formatted] }]);
    console.log("Tip received:", formatted);
    setTimeout(() => {
    const chatBox = document.querySelector(".feedback-chat");
    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
  }, 100);
  } else {
    console.warn("Empty or invalid tip", data);
  }

  } catch (err) {
    console.error("Feedback fetch failed", err);
  }
};

  const stopSession = async () => {
    if (ending) return; //  prevent multiple clicks
    setEnding(true);

    clearInterval(intervalRef.current);
    clearInterval(feedbackIntervalRef.current);
    const stream = videoRef.current?.srcObject;
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }

    try {
      const { data } = await axios.post("attention/end/", { session_id: sessionId });
      console.log(data.tip);
      localStorage.setItem("attention_report", JSON.stringify(data));
      navigate("/");
    } catch (err) {
      alert("Failed to end session. Please try again.");
      console.error(err);
      navigate("/");
    } finally {
      setEnding(false);
      navigate("/");
    }
  };

  return (
    <div className="live-view">
      <video ref={videoRef} autoPlay muted playsInline />
      <canvas ref={canvasRef} />

      {/*  feedback chat */}
      <div className="feedback-chat">
        <h3>🧠 Attention Coach</h3>
        {feedbackLog.map((entry, i) => (
          <div key={i} className="feedback-message">
            <div className="feedback-time">{entry.time}</div>
            <ul>
              {entry.tips.map((tip, idx) => (
                <li key={idx}>💡 {tip}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <button className="end-button" onClick={stopSession} disabled={ending}>End Session</button>
    </div>
  );
}
