import React, { useRef } from "react";
import "./Editor.css";

const Editor = ({
  darkMode,
  code,
  onChange,
  language,
  readOnly = false,
  panelRef,
}) => {
  return (
    <div className={`editor-section ${darkMode ? "dark" : "light"}`} ref={panelRef}>
      <div className="editor-header">
        <h2>{language} Code</h2>
      </div>
      <div className="editor-content">
        <textarea
          value={code}
          onChange={onChange}
          readOnly={readOnly}
          placeholder={readOnly ? "" : `Write ${language} Code Here...`}
          className="code-editor"
        />
      </div>
    </div>
  );
};

export default Editor;