// src/components/milestone1/LanguageSelector.jsx
import React from 'react';
import { Languages } from 'lucide-react';

export default function LanguageSelector({ value, onChange, disabled }) {
  return (
    <div className="flex items-center gap-2 bg-gray-800/60 p-3 rounded-lg border border-gray-700">
      <Languages size={20} className="text-indigo-400" />
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="bg-gray-900 text-white focus:outline-none w-full disabled:opacity-50 disabled:cursor-not-allowed rounded-md p-2 border border-gray-700"
      >
        <option value="auto">Auto-Detect Language</option>
        <option value="en-US">English (US)</option>
        <option value="en-IN">English (India)</option>
        <option value="hi-IN">Hindi (India)</option>
        <option value="ta-IN">Tamil (India)</option>
        <option value="te-IN">Telugu (India)</option>
        <option value="es-ES">Spanish (Spain)</option>
        <option value="fr-FR">French (France)</option>
        <option value="de-DE">German (Germany)</option>
      </select>
    </div>
  );
}