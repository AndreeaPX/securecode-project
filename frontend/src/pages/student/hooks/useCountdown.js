import { useEffect, useState, useRef } from "react";

export default function useCountdown(minutes, onExpire) {
  const [timeLeft, setTimeLeft] = useState(() => (minutes ? minutes * 60 : null));
  const expiredRef = useRef(false);

  useEffect(() => {
    if (!minutes) return;
    setTimeLeft(minutes * 60);
    expiredRef.current = false; 
  }, [minutes]);

  useEffect(() => {
    if (timeLeft == null) return;

    const interval = setInterval(() => {
      setTimeLeft(prev => {
        const next = prev - 1;
        if (next <= 0) {
          clearInterval(interval);
          if (!expiredRef.current) {
            onExpire?.();
            expiredRef.current = true;
          }
          return 0;
        }
        return next;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [timeLeft == null]); 

  const formatTime = () => {
    if (timeLeft == null) return "--:--";
    const min = Math.floor(timeLeft / 60).toString().padStart(2, "0");
    const sec = (timeLeft % 60).toString().padStart(2, "0");
    return `${min}:${sec}`;
  };

  return {
    timeLeft,
    formatted: formatTime(),
  };
}
