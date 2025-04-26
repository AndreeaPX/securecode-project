import { useEffect, useState } from "react";

function decodeJWT(token) {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return payload;
  } catch (e) {
    return null;
  }
}

export default function useTokenDebug() {
  const [info, setInfo] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("accessToken");
    if (!token) return;

    const payload = decodeJWT(token);
    if (!payload) {
      setInfo({ valid: false });
      return;
    }

    const expiresAt = new Date(payload.exp * 1000);
    const interval = setInterval(() => {
      const now = new Date();
      const secondsLeft = Math.floor((expiresAt - now) / 1000);
      setInfo({
        valid: secondsLeft > 0,
        secondsLeft,
        expiresAt: expiresAt.toLocaleString(),
        payload,
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return info;
}
