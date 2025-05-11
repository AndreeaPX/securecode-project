import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import axiosInstance from "../../../api/axios";
import { useAuth } from "../../../components/AuthProvider";
import "../../../styles/CreateQuestion.css";

export default function CreateQuestion() {
  const { questionId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [courses, setCourses] = useState([]);
  const [isEditMode, setIsEditMode] = useState(false);
  const [existingAttachment, setExistingAttachment] = useState(false);
  const [questionData, setQuestionData] = useState({
    text: "",
    type: "single",
    course: "",
    points: 1,
    options: [{ text: "", is_correct: false }],
    is_code_question: false,
    language: "",
    starter_code: "",
    expected_output: "",
  });
  const [attachmentFile, setAttachmentFile] = useState(null);

  let isRefreshingToken = false;
  let refreshPromise = null;

  const isTokenExpiringSoon = () => {
    const token = localStorage.getItem("accessToken");
    if (!token) return true;
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      const now = Math.floor(Date.now() / 1000);
      return payload.exp - now < 60;
    } catch {
      return true;
    }
  };

  const refreshAccessToken = async () => {
    if (isRefreshingToken && refreshPromise) return refreshPromise;
    const refreshToken = localStorage.getItem("refreshToken");
    if (!refreshToken) throw new Error("Refresh token missing");

    isRefreshingToken = true;
    refreshPromise = axios
      .post(`${import.meta.env.VITE_API_URL}token/refresh/`, { refresh: refreshToken }, { withCredentials: true })
      .then((res) => {
        const newAccessToken = res.data.access;
        const newRefreshToken = res.data.refresh;
        localStorage.setItem("accessToken", newAccessToken);
        if (newRefreshToken) {
          localStorage.setItem("refreshToken", newRefreshToken);
        }
      })
      .catch((err) => {
        console.error("Token refresh failed:", err);
        localStorage.clear();
        window.location.href = "/login?expired=true";
        throw err;
      })
      .finally(() => {
        isRefreshingToken = false;
        refreshPromise = null;
      });

    return refreshPromise;
  };

  useEffect(() => {
    if (!user) return;
    const init = async () => {
      try {
        if (isTokenExpiringSoon()) await refreshAccessToken();
        await fetchCourses();
        if (questionId) {
          setIsEditMode(true);
          await fetchQuestion(questionId);
        }
      } catch (err) {
        console.error("Token validation or fetch failed:", err);
        window.location.href = "/login?expired=true";
      }
    };
    init();
  }, [user, questionId]);

  const fetchCourses = async () => {
    const res = await axiosInstance.get("/courses/");
    setCourses(res.data);
  };

  const fetchQuestion = async (id) => {
    const res = await axiosInstance.get(`/questions/${id}/`);
    const q = res.data;
    setQuestionData({
      text: q.text,
      type: q.type,
      course: q.course,
      points: q.points,
      options: q.options?.length > 0 ? q.options : [{ text: "", is_correct: false }],
      is_code_question: q.type === "code",
      language: q.language || "",
      starter_code: q.starter_code || "",
      expected_output: q.expected_output || "",
    });
    setExistingAttachment(q.attachments?.length > 0);
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setQuestionData((prev) => ({ ...prev, [name]: type === "checkbox" ? checked : value }));
  };

  const handleOptionChange = (index, field, value) => {
    const newOptions = [...questionData.options];
    newOptions[index][field] = field === "is_correct" ? !newOptions[index][field] : value;
    setQuestionData((prev) => ({ ...prev, options: newOptions }));
  };

  const addOption = () => setQuestionData((prev) => ({ ...prev, options: [...prev.options, { text: "", is_correct: false }] }));

  const removeOption = (index) => {
    const newOptions = questionData.options.filter((_, i) => i !== index);
    setQuestionData((prev) => ({ ...prev, options: newOptions }));
  };

  const handleFileChange = (e) => setAttachmentFile(e.target.files[0]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (isTokenExpiringSoon()) await refreshAccessToken();

      const payload = {
        text: questionData.text,
        type: questionData.type,
        course: questionData.course,
        points: questionData.points,
        is_code_question: questionData.type === "code",
        language: questionData.type === "code" ? questionData.language : null,
        starter_code: questionData.type === "code" ? questionData.starter_code : null,
        expected_output: questionData.type === "code" ? questionData.expected_output : null,
        options: ["single", "multiple"].includes(questionData.type) ? questionData.options : [],
      };

      let res;
      if (isEditMode) {
        res = await axiosInstance.put(`/questions/${questionId}/`, payload);
        if (existingAttachment && attachmentFile) {
          await axiosInstance.delete(`/questions/${questionId}/attachments/`);
        }
      } else {
        res = await axiosInstance.post(`/questions/`, payload);
      }

      if (attachmentFile) {
        const formData = new FormData();
        formData.append("file", attachmentFile);
        await axiosInstance.post(`/questions/${res.data.id}/attachments/`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
      }

      alert(isEditMode ? "Question updated successfully!" : "Question created successfully!");
      navigate("/questions");
    } catch (err) {
      console.error("Submit failed:", err);
      alert("Error saving question.");
    }
  };

  return (
    <div className="create-question-page">
      <h2>{isEditMode ? "Edit Question" : "Create New Question"}</h2>
      <form onSubmit={handleSubmit} className="create-question-form">
        <textarea name="text" placeholder="Enter the question text" value={questionData.text} onChange={handleChange} required />
        <select name="type" value={questionData.type} onChange={handleChange}>
          <option value="single">Single Choice</option>
          <option value="multiple">Multiple Choice</option>
          <option value="open">Open Answer</option>
          <option value="code">Code Response</option>
        </select>
        <select name="course" value={questionData.course} onChange={handleChange} required>
          <option value="">Select Course</option>
          {courses.map((course) => (
            <option key={course.id} value={course.id}>{course.name}</option>
          ))}
        </select>
        <input type="number" name="points" placeholder="Points" value={questionData.points} onChange={handleChange} min={1} required />

        {["single", "multiple"].includes(questionData.type) && (
          <div className="options-section">
            <h4>Answer Options</h4>
            <p className="hint-text">
              {questionData.type === "single"
                ? "Select exactly one correct answer."
                : "Select one or more correct answers."}
            </p>
            {questionData.options.map((opt, index) => (
              <div key={index} className="option-item">
                <input type="text" placeholder="Option text" value={opt.text} onChange={(e) => handleOptionChange(index, "text", e.target.value)} required />
                <div className="correct-answer-toggle">
                  <input type="checkbox" checked={opt.is_correct} onChange={() => handleOptionChange(index, "is_correct")} />
                  <label>Correct Answer</label>
                </div>
                <button type="button" onClick={() => removeOption(index)}>Remove</button>
              </div>
            ))}
            <button type="button" onClick={addOption}>+ Add Option</button>
          </div>
        )}

        {questionData.type === "code" && (
          <>
            <select name="language" value={questionData.language} onChange={handleChange} required>
              <option value="">Select Language</option>
              <option value="python">Python</option>
              <option value="java">Java</option>
              <option value="c">C</option>
              <option value="cpp">C++</option>
              <option value="javascript">JavaScript</option>
              <option value="other">Other</option>
            </select>
            <textarea name="starter_code" placeholder="Starter code (optional)" value={questionData.starter_code} onChange={handleChange} />
            <textarea name="expected_output" placeholder="Expected output (optional)" value={questionData.expected_output} onChange={handleChange} />
          </>
        )}

        <input type="file" onChange={handleFileChange} />
        <button type="submit">{isEditMode ? "Update Question" : "Create Question"}</button>
      </form>
    </div>
  );
}
