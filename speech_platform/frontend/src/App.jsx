import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Milestone1 from './pages/Milestone1';
import Milestone2 from './pages/Milestone2';
import Milestone3 from './pages/Milestone3';
import Milestone4 from './pages/Milestone4';

function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Milestone1 />} />
          <Route path="milestone1" element={<Milestone1 />} />
          <Route path="milestone2" element={<Milestone2 />} />
          <Route path="milestone3" element={<Milestone3 />} />
          <Route path="milestone4" element={<Milestone4 />} />
        </Route>
      </Routes>
    </div>
  );
}

export default App;
