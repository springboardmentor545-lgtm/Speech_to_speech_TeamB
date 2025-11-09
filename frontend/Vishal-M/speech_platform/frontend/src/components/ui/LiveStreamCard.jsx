// src/components/ui/LiveStreamCard.jsx
import React from 'react';
import { Mic, MicOff } from 'lucide-react';
import GlassCard from './GlassCard';
import PrimaryButton from './PrimaryButton';
import SectionTitle from './SectionTitle';

export default function LiveStreamCard({ hook, title = "Live Transcription" }) {
  const { isStreaming, liveTranscript, error, startStreaming, stopStreaming } = hook;

  return (
    <GlassCard>
      <SectionTitle>{title}</SectionTitle>
      <div className="flex flex-col items-center gap-4">
        <PrimaryButton
          onClick={isStreaming ? stopStreaming : startStreaming}
          className="w-48"
        >
          {isStreaming ? <MicOff size={18} /> : <Mic size={18} />}
          <span>{isStreaming ? 'Stop Streaming' : 'Start Live Stream'}</span>
        </PrimaryButton>
        {isStreaming && (
          <div className="flex items-center gap-2 text-red-400">
            <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-sm">Streaming live...</span>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3 text-sm bg-red-500/20 text-red-300 rounded-lg border border-red-500">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="mt-4">
        <label className="block text-sm font-medium text-gray-300 mb-2">Live Transcript:</label>
        <textarea
          value={liveTranscript}
          readOnly
          className="w-full h-32 p-3 bg-gray-800 border border-gray-700 rounded-lg text-white resize-none"
          placeholder="Live transcription will appear here..."
        />
      </div>
    </GlassCard>
  );
}