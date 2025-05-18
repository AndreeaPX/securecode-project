import { useEffect, useState, useRef } from "react";
export default function useProctoring({ enabled, navigate }) {
  const [showOverlay, setShowOverlay] = useState(false);
  const retriesRef = useRef(1);
  const kickedRef = useRef(false);
  const timeoutRef = useRef(null);

  useEffect(() => {
    if (!enabled) return;

    const handleViolation = () => {
      clearTimeout(timeoutRef.current);

      if (retriesRef.current > 0) {
        setShowOverlay(true);
        timeoutRef.current = setTimeout(() => {
          if (!document.fullscreenElement && !kickedRef.current) {
            kickedRef.current = true;
            sessionStorage.setItem("proctoringKicked", "true");
            alert("You have been removed from the test.");
            navigate("/dashboard-student");
          }
        }, 5000);
      } else {
        if (!kickedRef.current) {
          kickedRef.current = true;
          sessionStorage.setItem("proctoringKicked", "true");
          alert("Second violation. Test ended.");
          navigate("/dashboard-student");
        }
      }
    };

    const handleFullscreenChange = () => {
      if (!document.fullscreenElement) handleViolation();
      else setShowOverlay(false);
    };

    const monitorSecondScreen = () => {
      const left = window.screenLeft || window.screenX;
      const width = window.screen.width;
      if (left < -100 || left > width + 100) handleViolation();
    };

    const disableKeys = (e) => {
      const key = e.key.toLowerCase();
      if ((e.ctrlKey || e.metaKey) && ["c", "v", "x", "u", "s"].includes(key)) {
        e.preventDefault();
      }
      if (["f12", "f11"].includes(key)) e.preventDefault();
    };

    const disablePaste = (e) => e.preventDefault();
    const disableContext = (e) => e.preventDefault();

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    document.addEventListener("keydown", disableKeys);
    window.addEventListener("paste", disablePaste);
    document.addEventListener("contextmenu", disableContext);

    const interval = setInterval(monitorSecondScreen, 3000);

    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
      document.removeEventListener("keydown", disableKeys);
      window.removeEventListener("paste", disablePaste);
      document.removeEventListener("contextmenu", disableContext);
      clearInterval(interval);
      clearTimeout(timeoutRef.current);
    };
  }, [enabled, navigate]);

  const reenterFullscreen = async () => {
    try {
      await document.documentElement.requestFullscreen();
      retriesRef.current = 0;
      setShowOverlay(false);
    } catch (err) {
      console.error("Can't re-enter fullscreen:", err);
    }
  };

  return { showOverlay, reenterFullscreen };
}
