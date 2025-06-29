import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axiosInstance from "../../../api/axios";
import "../../../styles/Review.css";

export default function AssignmentReview() {
  const { assignmentId } = useParams();
  const navigate = useNavigate();
  const [assignment, setAssignment] = useState(null);
  const [saving, setSaving] = useState(false);
  const [reviewComment, setReviewComment] = useState("");
  const autoGraded = assignment?.test_settings?.show_result;

  const settingLabels = {
  allow_sound_analysis: "Audio",
  use_proctoring: "Proctoring",
  has_ai_assistent: "AI Assistant",
  show_result: "Auto Graded"
  };

  useEffect(() => {
    axiosInstance.get(`/assignments/${assignmentId}/review/`).then(res => {
      setAssignment(res.data);
      setReviewComment(res.data.review_comment || "");
    });
  }, [assignmentId]);

  const handleAnswerChange = (idx, field, value) => {
    const updated = [...assignment.answers];
    updated[idx][field] = value;
    setAssignment({ ...assignment, answers: updated });
  };

  const handleSubmit = async () => {
  if (!reviewComment.trim()) {
    alert("Feedback is required.");
    return;
  }

  const autoGraded1 = assignment.test_settings.show_result;

  const answersPayload = assignment.answers.map(a => ({
    id: a.id,
    feedback: a.feedback,
    ...(autoGraded1 ? {} : { points: a.points })
  }));

    setSaving(true);
    try {
        await axiosInstance.put(`/assignments/${assignmentId}/review/`, {
        answers: answersPayload,
        review_comment: reviewComment,
        });
        navigate("/marks");
    } catch (err) {
        console.error("Failed to submit review", err);
    } finally {
        setSaving(false);
    }
    };


  if (!assignment) return <p>Loading assignment review...</p>;

  
  const optionTexts = (ids = [], options = []) => options.filter(opt => ids.includes(opt.id)).map(opt => opt.text);
  const totalPoints = assignment.answers.reduce((sum, a) => sum + (Number(a.points) || 0), 0);
  const exceedsMax = totalPoints > assignment.maxim_points;


  return (
    <div className="review-page">
      <h2>Review: {assignment.test_name} – {assignment.student_email}</h2>
        <section className="test-meta">
        <div className="meta-row">
            <p><strong>Attempt:</strong> {assignment.attempt_no}</p>
            <p><strong>Test Type:</strong> {assignment.test_type}</p>
            <p><strong>Auto Score:</strong> {assignment.auto_score ?? "N/A"}</p>
            <p><strong>Manual Score:</strong> {assignment.manual_score ?? "N/A"}</p>
        </div>

        <div className="settings-section">
            <ul className="settings-list">
            {Object.entries(assignment.test_settings).map(([key, value]) => (
                <li key={key} className={value ? "enabled" : "disabled"}>
                {settingLabels[key] || key}: {value ? "✅" : "❌"}
                </li>
            ))}
            </ul>
        </div>
        </section>


      {assignment.answers.map((a, idx) => (
        <div key={a.id} className="question-block">
          <h3>Q{idx + 1}: {a.question_text}</h3>
          <p><strong>Type:</strong> {a.question_type}</p>

          {a.attachments.length > 0 && (
            <div className="attachments">
              {a.attachments.map((att, i) => (
                att.is_image ? (
                  <img key={i} src={att.url} alt={att.filename} />
                ) : (
                  <a key={i} href={att.url} download>{att.filename}</a>
                )
              ))}
            </div>
          )}

          <div className="answer-box">
            <p><strong>Student Answer:</strong></p>
            {a.answer_text ? <pre>{a.answer_text}</pre> : <p>No text answer</p>}
            {a.selected_options?.length > 0 && (
            <p>
                <strong>Selected Options:</strong>{" "}
                {optionTexts(a.selected_options, a.options).join(", ")}
            </p>
            )}

            {a.correct_option_ids?.length > 0 && (
            <p>
                <strong>Correct Options:</strong>{" "}
                {optionTexts(a.correct_option_ids, a.options).join(", ")}
            </p>
            )}

            {a.expected_output && (
              <p><strong>Expected Output:</strong> {a.expected_output}</p>
            )}
          </div>

          <div className="grading-controls">
            <label>Points: <input type="number" value={a.points || ""} disabled={autoGraded} onChange={e => handleAnswerChange(idx, "points", parseFloat(e.target.value))} /></label>
            <label>Feedback (optional):<textarea value={a.feedback || ""} onChange={e => handleAnswerChange(idx, "feedback", e.target.value)} /></label>
          </div>
        </div>
      ))}

    <p className={exceedsMax ? "warning" : "info"}>
        Total Points: {totalPoints} / {assignment.maxim_points}
    </p>


      <div className="final-feedback">
        <label>Final Feedback (required):</label>
        <textarea value={reviewComment} onChange={(e) => setReviewComment(e.target.value)} />
      </div>


      <button onClick={handleSubmit} disabled={saving || exceedsMax}>Submit Review</button>
      {exceedsMax && (
        <p className="error-msg">Total assigned points exceed the allowed maximum.</p>
      )}
    </div>
  );
}
