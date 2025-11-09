// src/components/ui/Bar.jsx
import React from 'react';
export default function Bar({ value = 0 }) {
  return (
    <div className="w-full bg-gray-700/60 rounded h-2">
      <div className="h-2 rounded bg-indigo-500 transition-all" style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}