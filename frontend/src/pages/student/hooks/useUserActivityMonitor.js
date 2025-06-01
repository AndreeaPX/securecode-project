import { useEffect } from "react";
import axiosInstance from "../../../api/axios";

export default function useUserActivityMonitor(assignmentId) {
  useEffect(() => {
    if (!assignmentId) return;

    let lastKeyTime = null;

    const sendLog = async (eventType, message, score = 0.1) => {
      console.log("Sending event:", eventType, message);
      try {
        await axiosInstance.post("proctoring/mouse_keyboard_check/", {
          assignment_id: assignmentId,
          event_type: eventType,
          event_message: JSON.stringify(message),
          anomaly_score: score,
        });
      } catch (err) {
        console.log("Activity log on mouse and keyboard failed:", err?.response?.data || err.message);
      }
    };

    const handleKeyDown = (e) => {
      const now = Date.now();
      const delta = lastKeyTime ? now - lastKeyTime : null;
      lastKeyTime = now;

      sendLog("key_press", {
        key: e.key,
        ctrl: e.ctrlKey,
        meta: e.metaKey,
        shift: e.shiftKey,
        time_since_last: delta,
      });

      if (e.key === "Escape") {
        sendLog("esc_pressed", { key: e.key }, 0.9);
      }

      // Detect ctrl+c / ctrl+v / ctrl+x via keyboard
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "c") {
        sendLog("copy_event", { method: "keyboard" }, 0.6);
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "v") {
        sendLog("paste_event", { method: "keyboard" }, 0.8);
      } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "x") {
        sendLog("cut_event", { method: "keyboard" }, 0.6);
      }

      console.log("KEY:", e.key, "CTRL:", e.ctrlKey, "META:", e.metaKey);
    };

    const handlePaste = (e) => {
      const pasted = e.clipboardData.getData("text");
      sendLog("paste_event", {
        method: "mouse",
        pasted_text_length: pasted.length,
      }, 0.8);
    };

    const handleCopy = (e) => {
      const copied = window.getSelection()?.toString() || "";
      sendLog("copy_event", {
        method: "mouse",
        copied_text_length: copied.length,
      }, 0.6);
    };

    const handleCut = (e) => {
      const cut = window.getSelection()?.toString() || "";
      sendLog("cut_event", {
        method: "mouse",
        cut_text_length: cut.length,
      }, 0.6);
    };

    const handleMouseLeave = (e) => {
      if (!e.relatedTarget && !e.toElement) {
        sendLog("second_screen", { message: "Mouse left window. Possibly using another app or monitor." }, 0.8);
      }
    };

    const handleBlur = () => {
      sendLog("window_blur", { message: "Window lost focus" }, 0.6);
    };

    const handleFocus = () => {
      sendLog("window_focus", { message: "Window regained focus" });
    };

    const handleVisibilityChange = () => {
      if (document.hidden) {
        sendLog("tab_hidden", { message: "User switched tab" }, 0.7);
      } else {
        sendLog("tab_visible", { message: "User returned to tab" });
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    document.addEventListener("paste", handlePaste);
    document.addEventListener("copy", handleCopy);
    document.addEventListener("cut", handleCut);
    document.addEventListener("mouseleave", handleMouseLeave);
    window.addEventListener("blur", handleBlur);
    window.addEventListener("focus", handleFocus);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("paste", handlePaste);
      document.removeEventListener("copy", handleCopy);
      document.removeEventListener("cut", handleCut);
      document.removeEventListener("mouseleave", handleMouseLeave);
      window.removeEventListener("blur", handleBlur);
      window.removeEventListener("focus", handleFocus);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [assignmentId]);
}
