// src/components/milestone2/TranslationOutputColumn.jsx
import React from 'react';
import { Download, Globe, BarChart3, Clock } from 'lucide-react'; // Added icons
import GlassCard from '../ui/GlassCard';
import SectionTitle from '../ui/SectionTitle';

// We import MetricsTabs but no longer need MetricCard
import MetricsTabs from './MetricsTabs';

// Main Column Component
export default function TranslationOutputColumn({
  // Language props
  languages,
  selectedLanguage,
  onLanguageChange,
  // Translation props
  isTranslating,
  translatedText,
  // Segment props
  segmentState,
  onSegmentStateChange,
  applyGlossary,
  downloadTXT,
  // Metrics props
  metrics,
  metricsHistory,
  languageConfidence,
  // Details props
  detectedLanguage,
  transcriptId,
}) {
  return (
    <GlassCard>
      {/* --- Language Selector --- */}
      <div className="flex items-center justify-between mb-4">
        <SectionTitle>Translated Text</SectionTitle>
        <select
          value={selectedLanguage}
          onChange={(e) => onLanguageChange(e.target.value)}
          className="p-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
          disabled={segmentState === 'finalized'}
        >
          {languages.map((lang) => (
            <option key={lang.code} value={lang.code}>{lang.name}</option>
          ))}
        </select>
      </div>

      {/* --- Text Area --- */}
      {isTranslating ? (
        <div className="flex items-center justify-center h-40">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500" />
        </div>
      ) : (
        <textarea
          value={translatedText}
          readOnly
          className="w-full h-40 p-3 bg-gray-800 border border-gray-700 rounded-lg text-white resize-none"
          placeholder="Translated text will appear here..."
        />
      )}

      {/* --- Segment State Controls --- */}
      <div className="mt-4">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-sm font-medium text-gray-300">Segment State:</span>
          <span
            className={`px-2 py-1 rounded-full text-xs ${
              segmentState === 'draft'
                ? 'bg-yellow-500/20 text-yellow-400'
                : segmentState === 'finalized'
                ? 'bg-blue-500/20 text-blue-400'
                : 'bg-green-500/20 text-green-400'
            }`}
          >
            {segmentState.replace('-', ' ')}
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onSegmentStateChange('finalized')}
            className={`px-3 py-1 rounded text-sm ${segmentState === 'finalized'
              ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
          >
            Finalize
          </button>
          <button
            onClick={applyGlossary}
            disabled={!translatedText || segmentState === 'finalized'}
            className={`px-3 py-1 rounded text-sm ${segmentState === 'glossary-fixed'
              ? 'bg-green-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
          >
            Apply Glossary
          </button>
          <button
            onClick={downloadTXT}
            disabled={!translatedText}
            className="px-3 py-1 rounded text-sm bg-gray-800 text-gray-300 hover:bg-gray-700"
          >
            <Download size={14} className="inline mr-1" /> Download TXT
          </button>
        </div>
      </div>

      {/* --- ✅ NEW 4-CARD METRICS SECTION (from image) --- */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800/60 p-4 rounded-lg border border-gray-700 text-center">
          <BarChart3 size={20} className="mx-auto text-blue-400" />
          <div className="text-2xl font-bold text-green-400 mt-2">{(metrics.bleu ?? 0).toFixed(2)}</div>
          <div className="text-sm text-gray-500">BLEU</div>
        </div>
        <div className="bg-gray-800/60 p-4 rounded-lg border border-gray-700 text-center">
          <Clock size={20} className="mx-auto text-purple-400" />
          <div className="text-2xl font-bold text-blue-400 mt-2">{(metrics.latency_p95 ?? 0).toFixed(0)}ms</div>
          <div className="text-sm text-gray-500">Latency P95</div>
        </div>
        <div className="bg-gray-800/60 p-4 rounded-lg border border-gray-700 text-center">
          <Clock size={20} className="mx-auto text-pink-400" />
          <div className="text-2xl font-bold text-pink-400 mt-2">{(metrics.latency_p99 ?? 0).toFixed(0)}ms</div>
          <div className="text-sm text-gray-500">Latency P99</div>
        </div>
        <div className="bg-gray-800/60 p-4 rounded-lg border border-gray-700 text-center">
          <Globe size={20} className="mx-auto text-yellow-400" />
          <div className="text-2xl font-bold text-yellow-400 mt-2">{languages.length}+</div>
          <div className="text-sm text-gray-500">Languages</div>
        </div>
      </div>
      
      {/* --- Advanced Analytics Tabs (This renders the full section) --- */}
      <MetricsTabs
        metrics={metrics}
        metricsHistory={metricsHistory}
        languageConfidence={languageConfidence}
        translatedText={translatedText}
        detectedLanguage={detectedLanguage}
        targetLanguage={selectedLanguage}
        transcriptId={transcriptId}
        segmentState={segmentState}
      />
    </GlassCard>
  );
}