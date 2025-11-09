// src/components/milestone1/RecordingCard.jsx
import React from 'react';
import { Mic, MicOff } from 'lucide-react';
import GlassCard from '../ui/GlassCard';
import PrimaryButton from '../ui/PrimaryButton';

export default function RecordingCard({
  isRecording,
  stopRecording,
  startRecording,
  uploadingRecording,
  uploadProgress,
}) {
  return (
    <GlassCard>
      <h2 className="text-lg font-semibold mb-4">Live Recording</h2>
      <div className="flex flex-col items-center gap-4">
        <PrimaryButton
          onClick={isRecording ? stopRecording : startRecording}
          disabled={uploadingRecording}
          className="w-48"
        >
          {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
          <span>{isRecording ? 'Stop Recording' : 'Start Recording'}</span>
        </PrimaryButton>
        {isRecording && (
          <div className="flex items-center gap-2 text-red-400">
            <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-sm">Recording...</span>
          </div>
        )}
        {uploadingRecording && (
          <div className="mt-2 w-full">
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>{uploadProgress < 100 ? 'Uploading recording...' : 'Processing...'}</span>
              <span>{uploadProgress < 100 ? `${uploadProgress}%` : ''}</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="h-2 rounded-full transition-all duration-300 bg-indigo-500"
                style={{ width: `${uploadProgress < 100 ? uploadProgress : 100}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </GlassCard>
  );
}