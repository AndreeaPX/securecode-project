import React, { useState, useEffect } from "react";
import { useParams, useNavigate , useLocation} from "react-router-dom";
import axiosInstance from "../../../api/axios";
import { useAuth } from "../../../components/AuthProvider";
import "../../../styles/QuestionView.css";


export default function QuestionView({ readonly = true }) {
  const { questionId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const testIdFromQuery = params.get("test_id");
  const [questionData, setQuestionData] = useState(null);
  const [loading, setLoading] = useState(true);

  const [tests, setTests] = useState([]);
  const [selectedTestId, setSelectedTestId] = useState(testIdFromQuery || "");

  useEffect(() => {
    const fetchTests = async() => {
      try{
      if (user?.role === "professor") {
        const res = await axiosInstance.get("/tests/");
        setTests(res.data);
    }
  } catch (err){
    console.error("Failed to load tests", err);
  }
  };
  fetchTests();
},[user]);

  useEffect(() => {
    const fetchQuestion = async () => {
      try {
        const res = await axiosInstance.get(`/questions/${questionId}/`);
        const qData = res.data;
        setQuestionData(qData);

        if(user?.role === "professor"){
          const testsRes =  await axiosInstance.get("/tests/");
          const filteredTests = testsRes.data.filter(
            (test) => test.course === qData.course
          );
          setTests(filteredTests);
        }
      } catch (err) {
        console.error("Failed to fetch question or tests", err);
      } finally {
        setLoading(false);
      }
    };

    fetchQuestion();
  }, [questionId, user]);

  if (loading) return <p>Loading question...</p>;
  if (!questionData) return <p>Question not found.</p>;

  const handleAddToTest = async() => {
    if(!selectedTestId) return alert("Please select a test first.");
    try{
      await axiosInstance.post("/test-questions/", {
        test:parseInt(selectedTestId),
        question:parseInt(questionId),
        is_required: false,
        order:0
      });
      alert("Question added to test successfully!");
    }catch(err){
      console.error("Error adding question to test", err);
      alert("Failed to add question to test.");
    }
  };


  const {
    text,
    type,
    course,
    points,
    options = [],
    language,
    starter_code,
    expected_output,
    attachments = [],
    created_by,
    created_by_full_name,
    created_by_email,
  } = questionData;

  const isOwner = user?.id === created_by;

  return (
    <div className="question-view-page">
      <h2>Question Details</h2>

      <form className="question-view-form">
        <label>Question Text:</label>
        <textarea value={text} readOnly />

        <label>Type:</label>
        <select value={type} disabled>
          <option value="single">Single Choice</option>
          <option value="multiple">Multiple Choice</option>
          <option value="open">Open Answer</option>
          <option value="code">Code Response</option>
        </select>

        <label>Points:</label>
        <input type="number" value={points} readOnly />

        {["single", "multiple"].includes(type) && (
          <div className="options-section">
            <h4>Answer Options</h4>
            {options.map((opt, index) => (
              <div key={index} className="option-item">
                <input type="text" value={opt.text} readOnly />
                <div className="correct-answer-toggle">
                  <input type="checkbox" checked={opt.is_correct} readOnly />
                  <label>Correct</label>
                </div>
              </div>
            ))}
          </div>
        )}

        {type === "code" && (
          <>
            <label>Language:</label>
            <select value={language || ""} disabled>
              <option value="">Select Language</option>
              <option value="python">Python</option>
              <option value="java">Java</option>
              <option value="c">C</option>
              <option value="cpp">C++</option>
              <option value="javascript">JavaScript</option>
              <option value="other">Other</option>
            </select>

            <label>Starter Code:</label>
            <textarea value={starter_code || ""} readOnly />

            <label>Expected Output:</label>
            <textarea value={expected_output || ""} readOnly />
          </>
        )}

        {attachments.length > 0 && (
          <div>
            <h4>Attachments</h4>
            <ul>
              {attachments.map((file) => (
                <li key={file.id}>
                  <a href={file.file} target="_blank" rel="noopener noreferrer">
                    {file.file_type.toUpperCase()} File
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="question-meta">
          <p><strong>Created By:</strong> {created_by_full_name} ({created_by_email})</p>
        </div>

        {user?.role === "professor" && (
          <div className="test-integration-panel">
          <h4>Add to Test</h4>
          {testIdFromQuery ? (
            <>
            <p>Will add to test ID : {testIdFromQuery}</p>
            <button onClick={handleAddToTest}>Add to This Test</button>
            </>
          ):(
            <>
          <select
            value={selectedTestId}
            onChange={(e) => setSelectedTestId(e.target.value)}>
            <option value="">Select a test</option>
            {tests.map((t) => (
              <option key={t.id} value={t.id}>
                {t.name} - {t.type}
              </option>
            ))}
          </select>

          <button type="button" onClick={handleAddToTest} > Add to Test </button>

          {tests.length === 0 && (
            <p style={{ color: "#888", marginTop: "0.5rem" }}>
              No available tests for this course.
            </p>
       )}

        <button
          onClick={() => navigate(`/tests/create?course=${course}`)}> Create Test for this Course </button>
          </>
          )}
      </div>
      )}

        {!readonly && isOwner && (
          <button type="button" onClick={() => navigate(`/questions/edit/${questionId}`)}> Edit Question </button>
        )}
      </form>
    </div>
  );
}
