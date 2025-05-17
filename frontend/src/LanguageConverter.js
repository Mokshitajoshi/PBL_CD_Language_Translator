import React, { useState, useRef } from "react";

const LanguageConverter = () => {
  const [pythonCode, setPythonCode] = useState("");
  const [jsCode, setJsCode] = useState("// Converted JavaScript Code");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Refs for resizing
  const horizontalDividerRef = useRef(null);
  const rightPythonDividerRef = useRef(null);
  const rightJsDividerRef = useRef(null);
  const leftPanelRef = useRef(null);
  const rightPanelRef = useRef(null);
  const pythonCodeRef = useRef(null);
  const jsCodeRef = useRef(null);

  // Conversion function
  const handleConvert = async () => {
    if (!pythonCode.trim()) {
      setError("Please enter some Python code");
      return;
    }
    
    setLoading(true);
    setError("");
    
    try {
      console.log("Sending request to backend...");
      const response = await fetch('http://127.0.0.1:5000/convert', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ code: pythonCode }),
      });
      
      console.log("Response received:", response);
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("Data:", data);
      
      setJsCode(data.javascript || "// No JavaScript code generated");
    } catch (err) {
      console.error("Error:", err);
      setError(`Connection error: ${err.message}`);
      setJsCode("// Server connection failed");
    } finally {
      setLoading(false);
    }
  };

  // Resizing logic (unchanged)
  const handleHorizontalMouseDown = () => {
    document.addEventListener("mousemove", handleHorizontalMouseMove);
    document.addEventListener("mouseup", handleHorizontalMouseUp);
  };

  const handleHorizontalMouseMove = (e) => {
    const containerWidth = horizontalDividerRef.current.parentElement.clientWidth;
    const newLeftWidth = (e.clientX / containerWidth) * 100;
    
    if (newLeftWidth > 20 && newLeftWidth < 80) {
      leftPanelRef.current.style.flex = newLeftWidth + "%";
      rightPanelRef.current.style.flex = (100 - newLeftWidth) + "%";
    }
  };

  const handleHorizontalMouseUp = () => {
    document.removeEventListener("mousemove", handleHorizontalMouseMove);
    document.removeEventListener("mouseup", handleHorizontalMouseUp);
  };

  // Right Python Slider Logic
  const handlePythonRightMouseDown = () => {
    document.addEventListener("mousemove", handlePythonRightMouseMove);
    document.addEventListener("mouseup", handlePythonRightMouseUp);
  };

  const handlePythonRightMouseMove = (e) => {
    const containerWidth = rightPythonDividerRef.current.parentElement.clientWidth;
    const rect = rightPythonDividerRef.current.parentElement.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const newRightWidth = (mouseX / containerWidth) * 100;
    
    if (newRightWidth > 20 && newRightWidth < 80) {
      pythonCodeRef.current.style.width = newRightWidth + "%";
    }
  };

  const handlePythonRightMouseUp = () => {
    document.removeEventListener("mousemove", handlePythonRightMouseMove);
    document.removeEventListener("mouseup", handlePythonRightMouseUp);
  };

  // Right JavaScript Slider Logic
  const handleJsRightMouseDown = () => {
    document.addEventListener("mousemove", handleJsRightMouseMove);
    document.addEventListener("mouseup", handleJsRightMouseUp);
  };

  const handleJsRightMouseMove = (e) => {
    const containerWidth = rightJsDividerRef.current.parentElement.clientWidth;
    const rect = rightJsDividerRef.current.parentElement.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const newRightWidth = (mouseX / containerWidth) * 100;
    
    if (newRightWidth > 20 && newRightWidth < 80) {
      jsCodeRef.current.style.width = newRightWidth + "%";
    }
  };

  const handleJsRightMouseUp = () => {
    document.removeEventListener("mousemove", handleJsRightMouseMove);
    document.removeEventListener("mouseup", handleJsRightMouseUp);
  };

  return (
    <div className="app-container">
      <div className="navbar">Language Converter</div>

      <div className="container">
        {/* Python Code Editor */}
        <div className="editor-section" ref={leftPanelRef}>
          <div className="editor-wrapper">
            <h2>Python Code</h2>
            <div className="code-wrapper" ref={pythonCodeRef}>
              <textarea
                className="code-editor"
                value={pythonCode}
                onChange={(e) => setPythonCode(e.target.value)}
                placeholder="Write Python Code Here..."
              />
              <div 
                className="right-slider" 
                ref={rightPythonDividerRef} 
                onMouseDown={handlePythonRightMouseDown}
              ></div>
            </div>
          </div>
        </div>

        {/* Horizontal Resizable Splitter */}
        <div 
          className="splitter horizontal" 
          ref={horizontalDividerRef} 
          onMouseDown={handleHorizontalMouseDown}
        ></div>

        {/* JavaScript Code Editor */}
        <div className="editor-section" ref={rightPanelRef}>
          <div className="editor-wrapper">
            <h2>JavaScript Code</h2>
            <div className="code-wrapper" ref={jsCodeRef}>
              <textarea 
                className="code-editor"
                value={jsCode} 
                readOnly 
              />
              <div 
                className="right-slider" 
                ref={rightJsDividerRef} 
                onMouseDown={handleJsRightMouseDown}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* Convert Button - Centered */}
      <div className="convert-container">
        <button 
          className="convert-button" 
          onClick={handleConvert}
          disabled={loading}
        >
          {loading ? "Converting..." : "Convert"}
        </button>
      </div>
    </div>
  );
};

export default LanguageConverter;
