import React from "react";
import "./ConvertButton.css";

const ConvertButton = ({ darkMode, loading, onClick }) => {
  return (
    <div className="convert-container">
      <button
        className={`convert-button ${darkMode ? "dark" : "light"}`}
        onClick={onClick}
        disabled={loading}
      >
        {loading ? "Converting..." : "Convert"}
      </button>
    </div>
  );
};

export default ConvertButton;