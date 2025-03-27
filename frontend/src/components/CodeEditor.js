import React from "react";

const CodeEditor = ({ value, onChange, placeholder, isReadOnly }) => {
  return (
    <textarea
      className="w-full h-96 p-4 border rounded-lg bg-gray-100"
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      readOnly={isReadOnly}
    ></textarea>
  );
};

export default CodeEditor;
