// src/components/milestone1/TranscriptModal.jsx
import React from 'react';

export default function TranscriptModal({ transcript, onClose }) {
  if (!transcript) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-auto border border-gray-800 animate-slide-up"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold truncate pr-4">{transcript.filename}</h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white text-3xl leading-none"
            >
              &times;
            </button>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <p className="text-gray-300 whitespace-pre-wrap">
              {transcript.text || 'No text available.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}