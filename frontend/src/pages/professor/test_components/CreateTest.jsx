import React, { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axiosInstance from "../../../api/axios";
import { useAuth } from "../../../components/AuthProvider";
import "../../../styles/CreateTest.css";

export default function CreateTest({ editMode, viewMode }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { testId } = useParams();

  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [suggestedQuestions, setSuggestedQuestions] = useState([]);
  const [currentQuestions, setCurrentQuestions] = useState([]);
  const [selectedQuestionIds, setSelectedQuestionIds] = useState([]);
  const [initialQuestionsIds, setInitialQuestionsIds] = useState([]);
  const [availableSeries, setAvailableSeries] = useState([]);
  const [availableGroups, setAvailableGroups] = useState([]);

  const [testData, setTestData] = useState({
    name: "",
    type: "exam",
    course: "",
    start_time: "",
    deadline: "",
    duration_minutes: 60,
    allowed_attempts: 1,
    allow_copy_paste: false,
    use_proctoring: false,
    has_ai_assistent: false,
    show_result:false,
    maxim_points:90,
    extra_points:10,
    target_series: "",
    target_group: "",
    target_subgroup: "",
    is_submitted: false 
  });
  const isSubmitted = testData.is_submitted === true;
  const isReadOnly = viewMode || isSubmitted;
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!user) return;

    const init = async () => {
      try {
        const [coursesRes, profileRes] = await Promise.all([
          axiosInstance.get("/courses/"),
          axiosInstance.get("/settings/professor/")
        ]);

        setCourses(coursesRes.data);
        setAvailableSeries(profileRes.data.lecture_series || []);
        setAvailableGroups(profileRes.data.seminar_groups || []);

        if ((viewMode||editMode) && testId) {
          const testRes = await axiosInstance.get(`/tests/${testId}/`);
          const testDataRaw = testRes.data;

          setTestData({
            ...testDataRaw,
            target_series: testDataRaw.target_series || "",
            target_group: testDataRaw.target_group || "",
            is_submitted : testDataRaw.is_submitted || false
          });

          
          const testQuestionsRes = await axiosInstance.get(`/tests/${testId}/questions/`);
          const testQuestions = testQuestionsRes.data
            .map((tq) => tq.question)
            .filter((q) => q && String(q.course) === String(testDataRaw.course));

          const testQuestionIds = testQuestions.map((q) => q.id);

          setCurrentQuestions(testQuestions);
          setSelectedQuestionIds(testQuestionIds);
          setInitialQuestionsIds(testQuestionIds);

          const suggestedRes = await axiosInstance.get("/questions/", {
            params: {
              course: testDataRaw.course,
              ordering: "-created_at",
              limit: 20
            }
          });

          const suggested = suggestedRes.data.filter(
            (q) => !testQuestionIds.includes(q.id)
          );
          setSuggestedQuestions(suggested);
        } else {
          const draft = localStorage.getItem("testDraft");
          if (draft) {
            const parsed = JSON.parse(draft);
            if (parsed.name && parsed.course) {
              setTestData(parsed);
            } else {
              localStorage.removeItem("testDraft");
            }
          }
        }
      } catch (err) {
        console.error("Failed to load data:", err);
      } finally {
        setLoading(false);
      }
    };

    init();
  }, [user, editMode, testId]);

  useEffect(() => {
    console.log("Current Questions:", currentQuestions);
    const questionsWithAttachments = currentQuestions.filter(q => q.attachments && q.attachments.length > 0);
console.log("Questions with attachments:", questionsWithAttachments);
const hasDownloadableAttachments = currentQuestions.some((q) =>
  (q.attachments || []).some((a) => {
    
    const fileName = a?.file?.toLowerCase() || "";
    console.log(fileName)
    return !fileName.endsWith(".jpg") &&
           !fileName.endsWith(".jpeg") &&
           !fileName.endsWith(".png") &&
           !fileName.endsWith(".gif");
  })
  );
  if (hasDownloadableAttachments && testData.use_proctoring) {
    alert("Proctoring cannot be used with questions that require file downloads.");
    setTestData((prev) => ({ ...prev, use_proctoring: false }));
  }
  }, [currentQuestions, testData.use_proctoring]);

  


  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setTestData((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value
    }));
      
    if(testData.show_result){
      const onlyGrila = currentQuestions.every(
        (q) => q.type === "single" || q.type === "multiple"
      );
        if (!onlyGrila) {
      alert("You can only enable 'Show Result' for tests with single/multiple choice questions.");
      return;
    }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    //validations
    const start = new Date(testData.start_time);
    const end = new Date(testData.deadline);
    if(isNaN(start) || isNaN(end)){
      alert("Please add the start date and deadline for this test.");
      return;
    }
    if(start < new Date()){
      alert("The test must be in the future.");
      return;
    }

    const startH = start.getHours();
    const endH = end.getHours();

    if (startH < 7 || startH >= 24 || endH < 7 || endH >= 24){
      alert("Start and deadline times must be between 7 AM and 12 PM.");
      return;
    }

    const actualDuration = Math.floor((end-start)/(1000*60));
    if(testData.duration_minutes > actualDuration){
      alert("Duration exceeds the time window between start and deadline.");
      return;
    }

    const totalPoints = Number(testData.maxim_points) + Number(testData.extra_points);
    if(totalPoints !== 100){
      alert("The total points must be 100.");
      return;
    }

    if(testData.type !== "training" && Number(testData.allowed_attempts) !== 1){
      alert("Only training tests can have more than one attempt.");
      return;
    }

    if (testData.target_series && testData.target_group) {
       return alert("Please select either a series OR a group, not both.");
    }


    try {
      const payload = { ...testData };
      if (payload.type !== "training") {
        payload.allowed_attempts = 1;
      }

      if (editMode) {
        await axiosInstance.put(`/tests/${testId}/`, payload);

        const removed = initialQuestionsIds.filter(id => !selectedQuestionIds.includes(id));
        for (const qid of removed) {
            await axiosInstance.delete("/test-questions/by-composite/", {
                data: { test: testId, question: qid },
              });
        }

        const added = selectedQuestionIds.filter(id => !initialQuestionsIds.includes(id));
        for (let i = 0; i < added.length; i++) {
          await axiosInstance.post("/test-questions/", {
            test: testId,
            question: added[i],
            order: i,
            is_required: false
          });
        }

        alert("Test updated!");
        localStorage.removeItem("testDraft");
      } else {
        const res = await axiosInstance.post("/tests/", payload);
        const newTestId = res.data.id;

        for (let i = 0; i < selectedQuestionIds.length; i++) {
          await axiosInstance.post("/test-questions/", {
            test: newTestId,
            question: selectedQuestionIds[i],
            order: i,
            is_required: false
          });
        }

        alert("Test created!");
        localStorage.removeItem("testDraft");
      }

      navigate("/tests");
    } catch (err) {
      console.error("Failed to save test:", err);
      alert("Something went wrong.");
    }
  };

  const handleCourseChange = async (e) => {
    const courseId = e.target.value;
    setTestData((prev) => ({ ...prev, course: courseId }));

    try {
      const res = await axiosInstance.get("/questions/", {
        params: {
          course: courseId,
          ordering: "-created_at",
          limit: 5
        }
      });
      setSuggestedQuestions(res.data);
    } catch (err) {
      console.error("Failed to load suggested questions:", err);
    }
  };

  const handleSeeMoreQuestions = async () => {
    if (!testData.name || !testData.course || !testData.type) {
      return alert("Please fill in name, course and type first.");
    }

    let idToUse = testId;

    if (!editMode) {
      try {
        const res = await axiosInstance.post("/tests/", testData);
        idToUse = res.data.id;
        localStorage.removeItem("testDraft");
      } catch (err) {
        console.error("Failed to auto-save test:", err);
        return alert("Could not save test before viewing questions.");
      }
    }

    navigate(`/questions?course=${testData.course}&test_id=${idToUse}`);
  };

  if (loading) return <p>Loading test form...</p>;

  return (
  <div className="questions-page">
    <h2>{editMode ? "Edit Test" : "Create New Test"}</h2>
    <form onSubmit={handleSubmit} className="create-question-form">
      <fieldset disabled={isReadOnly} className="fieldset-wrapper">
        <input
          type="text"
          name="name"
          placeholder="Test Name"
          value={testData.name}
          onChange={handleChange}
          required
        />
        <select name="course" value={testData.course} onChange={handleCourseChange} required>
          <option value="">Select Course</option>
          {courses.map((course) => (
            <option key={course.id} value={course.id}>{course.name}</option>
          ))}
        </select>
        <select name="type" value={testData.type} onChange={handleChange} required>
          <option value="exam">Exam</option>
          <option value="seminar">Seminar</option>
          <option value="training">Training</option>
        </select>

        <label>Start Time</label>
        <input
          type="datetime-local"
          name="start_time"
          value={testData.start_time ? testData.start_time.slice(0, 16) : ""}
          onChange={handleChange}
        />

        <label>Deadline</label>
        <input
          type="datetime-local"
          name="deadline"
          value={testData.deadline ? testData.deadline.slice(0, 16) : ""}
          onChange={handleChange}
        />

        <input
          type="number"
          name="duration_minutes"
          placeholder="Duration (minutes)"
          value={testData.duration_minutes}
          onChange={handleChange}
          min={1}
        />

        <input
          type="number"
          name="maxim_points"
          placeholder="Total Points"
          value={testData.maxim_points}
          onChange={handleChange}
          min={0}
        />

        <input 
          type="number"
          name="extra_points"
          placeholder="Extra Points"
          value={testData.extra_points}
          onChange={handleChange}
          min={0}
        />

        {testData.type === "training" ? (
          <input
            type="number"
            name="allowed_attempts"
            placeholder="Allowed Attempts"
            value={testData.allowed_attempts || ""}
            onChange={handleChange}
            min={1}
          />
        ) : (
          <p className="info-text">Only 1 attempt is allowed for exams and official tests</p>
        )}

        <div className="checkbox-group">
          <label>
            <input
              type="checkbox"
              name="allow_copy_paste"
              checked={testData.allow_copy_paste}
              onChange={handleChange}
            />
            Allow Copy-Paste
          </label>
          <label>
            <input
              type="checkbox"
              name="use_proctoring"
              checked={testData.use_proctoring}
              onChange={handleChange}
            />
            Use Proctoring
          </label>
          <label>
            <input
              type="checkbox"
              name="has_ai_assistent"
              checked={testData.has_ai_assistent}
              onChange={handleChange}
            />
            Enable AI Assistant
          </label>
          <label>
            <input 
            type = "checkbox"
            name = "show_result"
            checked={testData.show_result}
            disabled={!currentQuestions.every(q => q.type === "single" || q.type === "multiple")}
            onChange={handleChange}
            />
            Show Result (auto-grade) Only for Quizzes
          </label>
        </div>

        <select
          name="target_series"
          value={testData.target_series?.id ||testData.target_series || ""}
          onChange={handleChange}
        >
          <option value="">Select Series</option>
          {availableSeries.map((series) => (
            <option key={series.id} value={series.id}>
              {series.name} - Y{series.year} ({series.specialization.name})
            </option>
          ))}
        </select>

        <select
          name="target_group"
          value={testData.target_group?.id || testData.target_group || ""}
          onChange={handleChange}
        >
          <option value="">Select Group</option>
          {availableGroups.map((group) => (
            <option key={group.id} value={group.id}>
              G{group.number} ({group.series.name} - Y{group.series.year})
            </option>
          ))}
        </select>

        <input
          type="number"
          name="target_subgroup"
          placeholder="Subgroup"
          value={testData.target_subgroup?.id || testData.target_subgroup || ""}
          onChange={handleChange}
        />

        

        {currentQuestions.length > 0 && (
          <div className="options-section">
            <h4>Current Questions</h4>
            {currentQuestions
              .filter((q) => selectedQuestionIds.includes(q.id))
              .map((q) => (
                <label key={`${q.id}-current`} className="question-label">
                  <input
                    type="checkbox"
                    checked={selectedQuestionIds.includes(q.id)}
                    onChange={(e) => {
                      const id = q.id;
                      const isChecked = e.target.checked;
                      setSelectedQuestionIds((prev) =>
                        isChecked ? [...prev, id] : prev.filter((qid) => qid !== id)
                      );
                    }}
                  />
                  {(q.text || "Untitled").slice(0, 100)}...
                </label>
              ))}
          </div>
        )}

        {!viewMode && suggestedQuestions.length > 0 && (
          <div className="options-section">
            <h4>Suggested Questions</h4>
            {suggestedQuestions.map((q) => (
              <label key={`${q.id}-suggested`} className="question-label">
                <input
                  type="checkbox"
                  value={q.id}
                  checked={selectedQuestionIds.includes(q.id)}
                  onChange={(e) => {
                    const id = parseInt(e.target.value);
                    setSelectedQuestionIds((prev) =>
                      e.target.checked
                        ? [...prev, id]
                        : prev.filter((qid) => qid !== id)
                    );
                  }}
                />
                {(q.text || "Untitled").slice(0, 100)}...
              </label>
            ))}
            
            <button
              type="button"
              className="submit-test-button"
              onClick={handleSeeMoreQuestions}
            >
              See More Questions
            </button>
          </div>
        )}

        </fieldset>
        {!viewMode && (
          <button type="submit" disabled={editMode && isSubmitted}>
            {editMode ? "Update Test" : "Create Test"}
          </button>
        )}

      {editMode && !viewMode && !isSubmitted && (
        <button
          type="button"
          className="submit-test-button"
          disabled={submitting}
          onClick={async () => {
            const confirmSubmit = window.confirm("Are you sure?");
            if (!confirmSubmit) return;
            setSubmitting(true);
            try {
              await axiosInstance.post(`/tests/${testId}/submit/`);
              alert("Test submitted to students!");
              navigate("/tests");
            } catch (err) {
              console.error("Submit failed:", err);
              alert("Submit failed. Try again.");
            } finally {
              setSubmitting(false);
            }
          }}
        >
          Submit to Students
        </button>
      )}
    </form>
    
  </div>
);
}