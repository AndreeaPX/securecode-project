import { useEffect, useState } from "react";

export default function useCountdown(minutes, onExpire) {
  const [timeLeft, setTimeLeft] = useState(() => (minutes ? minutes * 60 : null));

  useEffect(() => {
    if (!minutes) return;

    setTimeLeft(minutes * 60);
  }, [minutes]);

  useEffect(() => {
    if (timeLeft == null || timeLeft <= 0) return;

    const interval = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          clearInterval(interval);
          onExpire?.();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [timeLeft, onExpire]);

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
