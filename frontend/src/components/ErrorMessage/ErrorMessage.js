import React from "react";
import "./ErrorMessage.css";

const ErrorMessage = ({ darkMode, error }) => {
  if (!error) return null;

  return (
    <div className={`error-message ${darkMode ? "dark" : "light"}`}>
      {error}
    </div>
  );
};

export default ErrorMessage;