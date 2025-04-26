import React from "react";
import welcomeImg from "../../../images/welcome.png";
import "./Welcome.css";
import {useAuth} from "../../../components/AuthProvider";

export default function Welcome(){
    const {user} = useAuth();
    var procent = 80;
    var status_proc = "very good"

    return (
        <div className="welcome-container">
        <div className="welcome-text">
          <h2>
            Welcome back, <span className="highlight">{user.first_name} {user.last_name}!</span>
          </h2>
          <p>Your students completed <span className="highlight">{procent}</span>% of the tasks.</p>
          <p className="status">
            Progress is <span className="highlight good">{status_proc}!</span>
          </p>
        </div>
        <div className="welcome-image">
          <img src={welcomeImg} alt="Welcome" />
        </div>
      </div>
    );
};