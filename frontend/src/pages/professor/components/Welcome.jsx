import { useEffect, useState } from "react";
import welcomeImg from "../../../images/welcome.png";
import { useAuth }   from "../../../components/AuthProvider";
import axiosInstance from "../../../api/axios";
import "./Welcome.css";

const getStatusLabel = pct => {
  if (pct >= 90) return { txt: "excellent", cls: "great"  };
  if (pct >= 70) return { txt: "very good", cls: "good"   };
  if (pct >= 40) return { txt: "average",   cls: "okay"   };
  return { txt: "low",        cls: "bad"    };
};

export default function Welcome() {
  const { user } = useAuth();
  const [percent, setPercent] = useState(null); 

  useEffect(() => {
    axiosInstance.get("/assignments/overall-progress/")
      .then(res => {
        const { total, finished } = res.data;
        const pct = total ? Math.round((finished / total) * 100) : 0;
        setPercent(pct);
      })
      .catch(() => setPercent(0));
  }, []);

  const status = percent != null ? getStatusLabel(percent) : null;

  return (
    <div className="welcome-container">
      <div className="welcome-text">
        <h2>
          Welcome back,&nbsp;
          <span className="highlight">
            {user.first_name} {user.last_name}
          </span>!
        </h2>

        {percent == null ? (
          <p>Loading progress…</p>
        ) : (
          <>
            <p>
              Your students completed&nbsp;
              <span className="highlight">{percent}%</span> of their assignments.
            </p>
            <p className={`status ${status.cls}`}>
              Overall progress is <span className="highlight">{status.txt}</span>.
            </p>
          </>
        )}
      </div>

      <div className="welcome-image">
        <img src={welcomeImg} alt="Welcome visual" />
      </div>
    </div>
  );
}
