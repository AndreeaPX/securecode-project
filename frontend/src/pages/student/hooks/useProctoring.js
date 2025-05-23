import { useEffect, useState, useRef } from "react";

export default function useProctoring({ enabled, navigate }) {
  const [showOverlay, setShowOverlay] = useState(false);
  const retriesRef = useRef(1);
  const kickedRef = useRef(false);
  const timeoutRef = useRef(null);

  useEffect(() => {
    if (!enabled) return;

    const kickUser = (reason = "Violation") => {
      if (!kickedRef.current) {
        kickedRef.current = true;
        sessionStorage.setItem("proctoringKicked", "true");
        alert(`${reason}. You have been removed from the test.`);
        navigate("/dashboard-student");
      }
    };

    const handleViolation = () => {
      clearTimeout(timeoutRef.current);

      if (retriesRef.current > 0) {
        setShowOverlay(true);
        timeoutRef.current = setTimeout(() => {
          if (!document.fullscreenElement && !kickedRef.current) {
            kickUser("Fullscreen exit violation");
          }
        }, 5000);
        retriesRef.current--;
      } else {
        kickUser("Second violation");
      }
    };

    const handleFullscreenChange = () => {
      if (!document.fullscreenElement) handleViolation();
      else setShowOverlay(false);
    };

    const handleMouseLeave = (e) => {
      if (!e.relatedTarget && !e.toElement) {
        console.warn("Mouse exited window — possible second monitor usage. Please return to the test.");
        handleViolation();
      }
    };

    const handleWindowBlur = () => {
      console.warn("Window lost focus");
      handleViolation();
    };

    const disableKeys = (e) => {
      const key = e.key.toLowerCase();
      if ((e.ctrlKey || e.metaKey) && ["c", "v", "x", "u", "s", "a", "r", "p"].includes(key)) {
        e.preventDefault();
      }
      if (["f12", "f11", "escape"].includes(key)) {
        e.preventDefault();
      }
      if (e.altKey && (key === "tab" || key === "f4")) {
        e.preventDefault();
      }
    };

    const disablePaste = (e) => e.preventDefault();
    const disableContext = (e) => e.preventDefault();

    // Setup listeners
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    window.addEventListener("blur", handleWindowBlur);
    document.addEventListener("keydown", disableKeys);
    window.addEventListener("paste", disablePaste);
    document.addEventListener("contextmenu", disableContext);
    document.addEventListener("mouseleave", handleMouseLeave);

    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
      window.removeEventListener("blur", handleWindowBlur);
      document.removeEventListener("keydown", disableKeys);
      window.removeEventListener("paste", disablePaste);
      document.removeEventListener("contextmenu", disableContext);
      document.removeEventListener("mouseleave", handleMouseLeave);
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
