import React, {useEffect, useState} from "react";
import { useParams, useNavigate } from "react-router-dom";
import axiosInstance from "../../../api/axios";
import { useAuth } from "../../../components/AuthProvider";
import "../../../styles/StudentCourseTest.css";

export default function StudentCourseTest(){
    const {courseId} = useParams();
    const { user } = useAuth();
    const [tests, setTests] = useState([]);
    const navigate = useNavigate();
    useEffect(() => {
        //to do -> assigned tests

        const mockTest = [
            {
                id: 1,
                name: "Android Basics",
                type: "training",
                start_time: "2025-05-18T17:30:00Z",
                deadline: "2025-05-18T18:00:00Z",
                duration_minutes: 30,
                allowed_attempts: 1,
                allow_copy_paste: false,
                use_proctoring: true,
                has_ai_assistent: false,
                maxim_points: 90,
                extra_points: 10,
                target_series: "A",
                target_group: 1020,
                target_subgroup: 1,
                course: "4",
                professor: 42
            },
            {
                id: 2,
                name: "Java Basics",
                type: "training",
                start_time: "2025-05-19T10:40:00Z",
                deadline: "2025-05-26T20:40:00Z",
                duration_minutes: 60,
                allowed_attempts: 1,
                allow_copy_paste: true,
                use_proctoring: false,
                has_ai_assistent: false,
                maxim_points: 90,
                extra_points: 10,
                target_series: "A",
                target_group: 1000,
                target_subgroup: 1,
                course: "5",
                professor: 42
            },
            {
        id: 3,
        name: "JAVA DEMO",
        type: "exam",
        start_time: "2025-05-28T11:00:00Z",
        deadline: "2025-05-28T12:00:00Z",
        duration_minutes: 60,
        allowed_attempts: 1,
        allow_copy_paste: false,
        use_proctoring: false,
        has_ai_assistent: false,
        maxim_points: 90,
        extra_points: 10,
        created_at: "2025-05-14T20:13:28.200365Z",
        target_series: "A",
        target_group: 1024,
        target_subgroup: 2,
        course: 5,
        professor: 42
    }
        ];

        const filtered = mockTest.filter(test => String(test.course) === String(courseId));
        setTests(filtered);
    }, [courseId]);


    return (
        <div className="test-page-container">
        <h2 style={{ marginBottom: "2rem", color: "#e2d9ff" }}>Available Tests</h2>

        <div className="test-grid">
            {tests.length === 0 ? (
            <p>No available tests for this course.</p>
            ) : (
            tests.map((test) => (
                <div key={test.id} className="test-card">
                <div className="test-header">
                    <h3>{test.name}</h3>
                    <span>{test.type.toUpperCase()}</span>
                </div>

                <div className="test-details">
                    <p><strong>Duration:</strong> {test.duration_minutes} minutes</p>
                    <p>
                    <strong>Start:</strong> {new Date(test.start_time).toLocaleString("ro-RO", {timeZone: "UTC", hour12: false,})}
                    </p>
                    <p>
                    <strong>Deadline:</strong> {new Date(test.deadline).toLocaleString("ro-RO", {timeZone: "UTC", hour12: false,})}
                    </p>
                    <p>
                    <strong>Target:</strong> Series {test.target_series}, Group {test.target_group}, Subgroup {test.target_subgroup}
                    </p>
                </div>

                <div className="test-options">
                    {test.use_proctoring && <span>🔒 Proctoring Enabled</span>}
                    {test.has_ai_assistent && <span>🤖 AI Assistant</span>}
                    {test.allow_copy_paste && <span>📋 Copy-Paste Allowed</span>}
                </div>
                    <button onClick={() => navigate(`/tests/start/${test.id}`, { state: { test } })}>
                    Start Test
                    </button>
                </div>
            ))
            )}
            </div>
        </div>
    );

}