// src/utils/constants.js
export const LANGUAGES = [
  { code: 'es', name: 'Spanish' }, { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' }, { code: 'it', name: 'Italian' },
  { code: 'pt', name: 'Portuguese' }, { code: 'en-IN', name: 'English (India)' },
  { code: 'hi', name: 'Hindi' }, { code: 'ja', name: 'Japanese' },
  { code: 'ko', name: 'Korean' }, { code: 'ru', name: 'Russian' },
  { code: 'ar', name: 'Arabic' }, { code: 'zh', name: 'Chinese' },
  { code: 'nl', name: 'Dutch' }, { code: 'sv', name: 'Swedish' },
  { code: 'ta', name: 'Tamil' }, { code: 'te', name: 'Telugu' },
  { code: 'th', name: 'Thai' }, { code: 'tr', name: 'Turkish' },
  { code: 'vi', name: 'Vietnamese' }, { code: 'id', name: 'Indonesian' },
  { code: 'ms', name: 'Malay' },
];

export const SOURCE_LANGUAGES = [
  { code: 'auto', name: 'Auto-Detect' },
  { code: 'en-US', name: 'English (US)' }, { code: 'en-IN', name: 'English (India)' },
  { code: 'hi-IN', name: 'Hindi (India)' }, { code: 'ta-IN', name: 'Tamil (India)' },
  { code: 'te-IN', name: 'Telugu (India)' }, { code: 'es-ES', name: 'Spanish (Spain)' },
  { code: 'fr-FR', name: 'French (France)' }, { code: 'de-DE', name: 'German (Germany)' },
];

export const INITIAL_GLOSSARY_RULES = [
  { source_term: 'AI', target_term: 'IA', language_pair: 'en-es' },
  { source_term: 'real-time', target_term: 'tiempo real', language_pair: 'en-es' },
  { source_term: 'platform', target_term: 'plataforma', language_pair: 'en-es' },
  { source_term: 'AI', target_term: 'IA', language_pair: 'en-fr' },
  { source_term: 'real-time', target_term: 'temps réel', language_pair: 'en-fr' },
];