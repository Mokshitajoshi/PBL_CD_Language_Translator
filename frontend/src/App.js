import React, { useState } from "react";
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
        />
        
        <Editor
          darkMode={darkMode}
          code={jsCode}
          readOnly={true}
          language="JavaScript"
        />
      </div>
      
      <div className="controls">
        <ConvertButton onClick={handleConvert} loading={loading} darkMode={darkMode} />
        {error && <ErrorMessage message={error} />}
      </div>
    </div>
  );
};

export default App;
