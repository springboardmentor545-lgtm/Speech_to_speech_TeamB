// src/components/milestone2/MetricsTabs.jsx
import React, { useState } from 'react';
import { Info } from 'lucide-react';
import Bar from '../ui/Bar'; 
import { 
  readabilityScore, 
  qualityVerdict, 
  estimateNGramPrecision 
} from '../../utils/analytics'; 

export default function MetricsTabs({
  metrics,
  languageConfidence,
  translatedText,
  metricsHistory,
  detectedLanguage,
  targetLanguage,
  transcriptId,
  segmentState,
}) {
  const [tab, setTab] = useState('quality');

  // Helper data objects for clean rendering
  const qualityData = {
    bleu: metrics.bleu ?? 0,
    confidence: (metrics.confidence ?? languageConfidence ?? 0.9) * 100,
    readability: metrics.readability ?? readabilityScore(translatedText),
    verdict: metrics.verdict ?? qualityVerdict({
      bleu: metrics.bleu ?? 0,
      readability: metrics.readability ?? readabilityScore(translatedText),
      confidence: metrics.confidence ?? languageConfidence ?? 0.9
    })
  };

  const precisionData = {
    p1: (metrics.precision?.p1) ?? estimateNGramPrecision(translatedText).p1,
    p2: (metrics.precision?.p2) ?? estimateNGramPrecision(translatedText).p2,
    p3: (metrics.precision?.p3) ?? estimateNGramPrecision(translatedText).p3,
    p4: (metrics.precision?.p4) ?? estimateNGramPrecision(translatedText).p4,
  };

  return (
    <div className="mt-6">
      <div className="flex gap-2 border-b border-gray-700 pb-2">
        {['quality', 'performance', 'analytics', 'details'].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-1 rounded-t ${
              tab === t 
              ? 'bg-gray-800 text-white border border-gray-700 border-b-transparent' 
              : 'text-gray-300 hover:text-white'
            }`}
          >
            {t[0].toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {/* --- QUALITY TAB --- */}
      {tab === 'quality' && (
        <div className="bg-gray-900/40 p-4 border border-gray-700 rounded-b">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <div className="text-xs text-gray-400 mb-1">BLEU</div>
              <div className="text-3xl font-bold">{qualityData.bleu.toFixed(2)}</div>
            </div>
            <div>
              <div className="text-xs text-gray-400 mb-1">Language Confidence</div>
              <div className="text-3xl font-bold">{qualityData.confidence.toFixed(1)}%</div>
            </div>
            <div>
              <div className="text-xs text-gray-400 mb-1">Readability</div>
              <div className="text-3xl font-bold">{qualityData.readability.toFixed(0)}</div>
            </div>
            <div>
              <div className="text-xs text-gray-400 mb-1">Verdict</div>
              <div className="text-xl font-bold">{qualityData.verdict}</div>
            </div>
          </div>
        </div>
      )}

      {/* --- PERFORMANCE TAB --- */}
      {tab === 'performance' && (
        <div className="bg-gray-900/40 p-4 border border-gray-700 rounded-b space-y-3">
          <div className="text-sm text-gray-300">Recent Translation Latencies</div>
          <div className="space-y-2">
            {metricsHistory && metricsHistory.length > 0 ? (
              metricsHistory.slice(-8).map((m, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="text-xs w-28 text-gray-400">{new Date(m.t).toLocaleTimeString()}</div>
                  <Bar value={Math.min(100, (m.latency / Math.max(1, metrics.latency_p99 || 400)) * 100)} />
                  <div className="text-xs w-14 text-right text-gray-300">{m.latency.toFixed(0)} ms</div>
                </div>
              ))
            ) : (
              <div className="text-gray-500 text-sm">No data yet. Translate to populate.</div>
            )}
          </div>
        </div>
      )}

      {/* --- ANALYTICS TAB --- */}
      {tab === 'analytics' && (
        <div className="bg-gray-900/40 p-4 border border-gray-700 rounded-b">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(precisionData).map(([key, value]) => (
              <div key={key}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-300">{key.replace('p', '')}-gram precision</span>
                  <span className="text-sm text-gray-400">{value.toFixed(1)}%</span>
                </div>
                <Bar value={value} />
              </div>
            ))}
          </div>
          <div className="mt-3 text-xs text-gray-400 flex items-center gap-2">
            <Info size={14} /> 
            True n-gram precision needs a reference translation; these are placeholders.
          </div>
        </div>
      )}

      {/* --- DETAILS TAB --- */}
      {tab === 'details' && (
        <div className="bg-gray-900/40 p-4 border border-gray-700 rounded-b grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="space-y-1">
            <div><span className="text-gray-400">Detected Language:</span> <strong>{detectedLanguage || '-'}</strong></div>
            <div><span className="text-gray-400">Confidence:</span> <strong>{qualityData.confidence.toFixed(1)}%</strong></div>
            <div><span className="text-gray-400">Target Language:</span> <strong>{targetLanguage || '-'}</strong></div>
            <div><span className="text-gray-400">Transcript ID:</span> <strong>{transcriptId || '-'}</strong></div>
          </div>
          <div className="space-y-1">
            <div><span className="text-gray-400">Segment State:</span> <strong>{segmentState}</strong></div>
            <div><span className="text-gray-400">P95:</span> <strong>{(metrics.latency_p95 ?? 0).toFixed(0)} ms</strong></div>
            <div><span className="text-gray-400">P99:</span> <strong>{(metrics.latency_p99 ?? 0).toFixed(0)} ms</strong></div>
            <div><span className="text-gray-400">BLEU:</span> <strong>{(metrics.bleu ?? 0).toFixed(2)}</strong></div>
          </div>
        </div>
      )}
    </div>
  );
}