// src/components/milestone1/TranscriptsTable.jsx
import React from 'react';
import { Download, CheckCircle, AlertCircle, Clock, FileText } from 'lucide-react';
import GlassCard from '../ui/GlassCard';
import PrimaryButton from '../ui/PrimaryButton';

const getStatusIcon = (status) => {
  switch (status) {
    case 'completed': return <CheckCircle size={16} className="text-green-500" />;
    case 'processing': return <Clock size={16} className="text-yellow-500 animate-spin" />;
    case 'failed': return <AlertCircle size={16} className="text-red-500" />;
    case 'queued': return <Clock size={16} className="text-gray-500" />;
    default: return <FileText size={16} className="text-gray-500" />;
  }
};

const displayLanguage = (t) => {
  if (t.status === 'processing' || t.status === 'queued') return <span className="text-gray-400 italic">Detecting...</span>;
  if (t.language && t.language.startsWith('unknown')) return <span className="text-yellow-400 italic">Auto-Detect</span>;
  return t.language;
};

export default function TranscriptsTable({ transcripts, exportCSV, onSelectTranscript }) {
  if (transcripts.length === 0) return null;

  return (
    <GlassCard>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Transcripts</h2>
        <PrimaryButton onClick={exportCSV}>
          <Download size={16} />
          Export CSV
        </PrimaryButton>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="text-left py-3 px-4 text-gray-300">ID</th>
              <th className="text-left py-3 px-4 text-gray-300">Filename</th>
              <th className="text-left py-3 px-4 text-gray-300">Status</th>
              <th className="text-left py-3 px-4 text-gray-300">Language</th>
              <th className="text-left py-3 px-4 text-gray-300">Actions</th>
            </tr>
          </thead>
          <tbody>
            {transcripts.map((t) => (
              <tr key={t.id} className="border-b border-gray-800 hover:bg-white/5">
                <td className="py-3 px-4 text-gray-300">{t.id}</td>
                <td className="py-3 px-4 text-gray-300 truncate max-w-xs">{t.filename}</td>
                <td className="py-3 px-4">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(t.status)}
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      t.status === 'completed'
                        ? 'bg-green-500/20 text-green-400'
                        : (t.status === 'processing' || t.status === 'queued')
                        ? 'bg-yellow-500/20 text-yellow-400'
                        : 'bg-red-500/20 text-red-400'
                    }`}>
                      {t.status}
                    </span>
                  </div>
                </td>
                <td className="py-3 px-4 text-gray-300">{displayLanguage(t)}</td>
                <td className="py-3 px-4">
                  <button
                    onClick={() => onSelectTranscript(t)}
                    className="text-indigo-400 hover:text-indigo-300 mr-3 disabled:text-gray-500 disabled:cursor-not-allowed"
                    disabled={t.status !== 'completed'}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </GlassCard>
  );
}