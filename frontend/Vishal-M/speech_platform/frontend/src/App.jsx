import React from "react";
import { Routes, Route } from "react-router-dom";

import Layout from "./components/Layout";
import Milestone1 from "./pages/Milestone1";
import Milestone2 from "./pages/Milestone2";

import GradientBackground from "./components/ui/GradientBackground"; // ✅ only once

function App() {
  return (
    <GradientBackground>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Milestone1 />} />
          <Route path="milestone1" element={<Milestone1 />} />
          <Route path="milestone2" element={<Milestone2 />} />
        </Route>
      </Routes>
    </GradientBackground>
  );
}

export default App;
