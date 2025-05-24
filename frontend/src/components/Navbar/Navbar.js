import React from "react";
import "./Navbar.css";

const Navbar = ({ darkMode }) => {
  return (
    <div className={`navbar ${darkMode ? "dark" : "light"}`}>
      <h1>Language Converter</h1>
    </div>
  );
};

export default Navbar;