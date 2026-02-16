import React from "react";
import ReactDOM from "react-dom/client";
import DynamicalSystemSimulator from "./DynamicalSystemSimulator";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <DynamicalSystemSimulator />
  </React.StrictMode>
);
