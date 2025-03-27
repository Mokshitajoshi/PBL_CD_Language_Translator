import React from "react";

const Buttons = ({ onConvert }) => {
  return (
    <div className="buttons">
      <button className="convert-btn" onClick={onConvert}>
        Convert Language
      </button>
      <button className="compiler-btn">
        Compiler
      </button>
    </div>
  );
};

export default Buttons;
