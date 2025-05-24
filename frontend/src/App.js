import React, { useState, useRef } from "react";
import DarkModeToggle from "./components/DarkModeToggle/DarkModeToggle";
import Navbar from "./components/Navbar/Navbar";
import Editor from "./components/Editor/Editor";
import ConvertButton from "./components/ConvertButton/ConvertButton";
import ErrorMessage from "./components/ErrorMessage/ErrorMessage";
import "./App.css";

const App = () => {
  const [pythonCode, setPythonCode] = useState("");
  const [jsCode, setJsCode] = useState("// Converted JavaScript Code");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [darkMode, setDarkMode] = useState(true);

  const horizontalDividerRef = useRef(null);
  const leftPanelRef = useRef(null);
  const rightPanelRef = useRef(null);

  const handleConvert = async () => {
    if (!pythonCode.trim()) {
      setError("Please enter some Python code");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://127.0.0.1:5000/convert", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ code: pythonCode }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      setJsCode(data.javascript || "// No JavaScript code generated");
    } catch (err) {
      setError(`Connection error: ${err.message}`);
      setJsCode("// Server connection failed");
    } finally {
      setLoading(false);
    }
  };

  const handleHorizontalMouseDown = () => {
    document.addEventListener("mousemove", handleHorizontalMouseMove);
    document.addEventListener("mouseup", handleHorizontalMouseUp);
  };

  const handleHorizontalMouseMove = (e) => {
    const containerWidth =
      horizontalDividerRef.current.parentElement.clientWidth;
    const newLeftWidth = (e.clientX / containerWidth) * 100;

    if (newLeftWidth > 20 && newLeftWidth < 80) {
      leftPanelRef.current.style.flex = newLeftWidth + "%";
      rightPanelRef.current.style.flex = 100 - newLeftWidth + "%";
    }
  };

  const handleHorizontalMouseUp = () => {
    document.removeEventListener("mousemove", handleHorizontalMouseMove);
    document.removeEventListener("mouseup", handleHorizontalMouseUp);
  };

  return (
    <div className={`app-container ${darkMode ? "dark" : "light"}`}>
      <DarkModeToggle darkMode={darkMode} toggleDarkMode={() => setDarkMode(!darkMode)} />
      <Navbar darkMode={darkMode} />
      
      <div className="editor-container">
        <Editor
          darkMode={darkMode}
          code={pythonCode}
          onChange={(e) => setPythonCode(e.target.value)}
          language="Python"
          panelRef={leftPanelRef}
        />
        
        <div
          className={`splitter horizontal ${darkMode ? "dark" : "light"}`}
          ref={horizontalDividerRef}
          onMouseDown={handleHorizontalMouseDown}
        ></div>
        
        <Editor
          darkMode={darkMode}
          code={jsCode}
          readOnly={true}
          language="JavaScript"
          panelRef={rightPanelRef}
        />
      </div>

      <ErrorMessage darkMode={darkMode} error={error} />
      <ConvertButton darkMode={darkMode} loading={loading} onClick={handleConvert} />
    </div>
  );
};

export default App;