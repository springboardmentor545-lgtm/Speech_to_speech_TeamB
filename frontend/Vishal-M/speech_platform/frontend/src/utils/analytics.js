// src/utils/analytics.js

// Flesch Reading Ease (approx, assumes English text)
export function readabilityScore(text = '') {
  const sentences = Math.max(1, (text.match(/[.!?]/g) || []).length);
  const words = Math.max(1, (text.trim().split(/\s+/).filter(Boolean).length));
  const syllables = Math.max(1, (text.match(/[aeiouy]+/gi) || []).length);
  const ASL = words / sentences; // avg sentence length
  const ASW = syllables / words; // avg syllables per word
  const score = 206.835 - (1.015 * ASL) - (84.6 * ASW);
  return Math.max(0, Math.min(100, score));
}

// Basic “quality verdict” based on BLEU-ish + readability + confidence
export function qualityVerdict({ bleu = 0, readability = 50, confidence = 0.9 }) {
  const composite = (bleu / 100) * 0.6 + (readability / 100) * 0.25 + (confidence) * 0.15;
  if (composite >= 0.8) return 'Excellent';
  if (composite >= 0.6) return 'Good';
  if (composite >= 0.4) return 'Fair';
  return 'Poor';
}

// Very rough n-gram “precision” placeholders if server doesn’t return them
export function estimateNGramPrecision(text = '') {
  const len = Math.max(1, text.trim().split(/\s+/).length);
  const base = Math.max(40, Math.min(95, 100 - Math.log(len + 1) * 10));
  return {
    p1: base,
    p2: base - 8,
    p3: base - 15,
    p4: base - 22,
  };
}