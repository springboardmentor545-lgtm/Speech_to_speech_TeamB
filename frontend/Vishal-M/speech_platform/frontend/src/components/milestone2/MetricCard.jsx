// src/components/milestone2/MetricCard.jsx
import React from "react";
// We remove the import for MetricsTabs

export default function MetricCard({ title, value, unit, latency, p50, p95, p99 }) {
  return (
    <div className="bg-gray-900/60 rounded-xl p-5 border border-gray-700 backdrop-blur-xl shadow-xl hover:shadow-2xl transition-all ease-in-out">
      <h3 className="text-gray-300 text-sm font-medium mb-1">{title}</h3>

      <p className="text-white text-3xl font-bold">
        {value} {unit && <span className="text-gray-400 text-xl">{unit}</span>}
      </p>

      {/* Latency Metrics (Only displayed if provided) */}
      {(latency || p50 || p95 || p99) && (
        <div className="mt-3 text-sm text-gray-400 space-y-1">
          {latency && <p>Latency Avg: <span className="text-indigo-400">{latency} ms</span></p>}
          {p50 && <p>P50: <span className="text-indigo-400">{p50} ms</span></p>}
          {p95 && <p>P95: <span className="text-indigo-400">{p95} ms</span></p>}
          {p99 && <p>P99: <span className="text-indigo-400">{p99} ms</span></p>}
        </div>
      )}

      {/* The MetricsTabs component was removed from here */}
    </div>
  );
}