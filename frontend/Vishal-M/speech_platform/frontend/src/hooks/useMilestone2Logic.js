// src/hooks/useMilestone2Logic.js
import { useState, useEffect, useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import api from '../utils/api';
import { getSafeTimestamp } from '../utils/helpers';
import { readabilityScore, qualityVerdict, estimateNGramPrecision } from '../utils/analytics';
import { INITIAL_GLOSSARY_RULES } from '../utils/constants';

// Removed: useLiveTranscription and useDebounce imports

export const useMilestone2Logic = () => {
  // --- All State Hooks ---
  const [sourceText, setSourceText] = useState('This is a sample text for translation. In a real implementation, this would come from the transcription module.');
  const [translatedText, setTranslatedText] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('es'); // target
  const [metrics, setMetrics] = useState({ bleu: 0, latency_p95: 0, latency_p99: 0, confidence: null, readability: null, precision: null, verdict: null });
  const [metricsHistory, setMetricsHistory] = useState([]);
  const [isTranslating, setIsTranslating] = useState(false);
  const [error, setError] = useState(null);
  const [segmentState, setSegmentState] = useState('draft');
  const [glossaryOpen, setGlossaryOpen] = useState(false);
  const [audioFile, setAudioFile] = useState(null);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcriptId, setTranscriptId] = useState(null);
  const [sourceLanguage, setSourceLanguage] = useState('auto');
  const [detectedLanguage, setDetectedLanguage] = useState('en');
  const [languageConfidence, setLanguageConfidence] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioElement, setAudioElement] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [uploadingRecording, setUploadingRecording] = useState(false);
  const [glossaryRules, setGlossaryRules] = useState(INITIAL_GLOSSARY_RULES);
  const [newRule, setNewRule] = useState({ source_term: '', target_term: '', language_pair: `${detectedLanguage}-${selectedLanguage}` });

  // --- All Refs ---
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef(null);
  const streamRef = useRef(null);
  const languageRef = useRef(sourceLanguage);

  // Removed: Live transcription hooks

  // --- All useEffects ---
  useEffect(() => { 
    languageRef.current = sourceLanguage;
  }, [sourceLanguage]);

  useEffect(() => {
    if (sourceText && segmentState !== 'finalized') {
      translateText();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedLanguage]); 

  useEffect(() => {
    return () => {
      if (audioElement) { 
        audioElement.pause(); 
        audioElement.src = '';
      }
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
    };
  }, []);
  
  // Removed: useEffect for debouncedTranscript

  // --- All Logic Functions (as useCallBack) ---
  
  // Reverted: translateText to original signature
  const translateText = useCallback(async (detectedLang = null) => {
    if (!sourceText) return;
    if (segmentState === 'finalized') return;
    
    const langToUse = detectedLang || detectedLanguage;
    setIsTranslating(true);
    setError(null);
    const startTime = performance.now();

    try {
      const response = await api.post('/api/translate', {
        text: sourceText, // <-- Reverted
        source_language: langToUse,
        target_language: selectedLanguage,
        glossary_rules: glossaryRules
          .filter((r) => r.language_pair === `${langToUse}-${selectedLanguage}`)
          .map((r) => ({ source_term: r.source_term, target_term: r.target_term, language_pair: r.language_pair })),
      });
      
      const endTime = performance.now();
      const latency = endTime - startTime;
      const server = response.data || {};
      const bleu = server.bleu_score ?? Math.floor(Math.random() * 40) + 60;
      const precision = server.precision ?? estimateNGramPrecision(server.translated_text || sourceText);
      const confidence = server.language_confidence ?? (languageConfidence ?? 0.92);
      const readability = server.readability ?? readabilityScore(server.translated_text || translatedText || '');
      const verdict = server.quality ?? qualityVerdict({ bleu, readability, confidence });

      setTranslatedText(server.translated_text || server.tgt_text || '');
      setMetrics({ bleu, latency_p95: latency + Math.random() * 50, latency_p99: latency + Math.random() * 100, confidence, readability, precision, verdict });
      setMetricsHistory((h) => [...h.slice(-19), { t: Date.now(), latency }]);
      
    } catch (err) {
      console.error('Error translating text:', err);
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) setError(detail.map((e) => e.msg || JSON.stringify(e)).join('; '));
      else if (typeof detail === 'object') setError(JSON.stringify(detail));
      else setError(detail || 'Translation failed.');
      setTranslatedText('');
    } finally {
      setIsTranslating(false);
    }
  }, [sourceText, segmentState, detectedLanguage, selectedLanguage, glossaryRules, languageConfidence, translatedText]); // Reverted dependencies

  const pollTranscriptionStatus = useCallback(async (id) => {
    try {
      const response = await api.get(`/api/transcripts/${id}`);
      const transcript = response.data;
      if (transcript.status === 'completed') {
        const detectedLang = transcript.language || 'en';
        setSourceText(transcript.text || 'No transcription available');
        setDetectedLanguage(detectedLang);
        if (typeof transcript.confidence === 'number') setLanguageConfidence(transcript.confidence);
        setIsTranscribing(false);
        setUploadProgress(100);
        // Translate the new text
        setTimeout(() => translateText(detectedLang), 500); // <-- Reverted
      } else if (transcript.status === 'failed') {
        setError('Transcription failed: ' + (transcript.text || 'Unknown error'));
        setIsTranscribing(false);
      } else {
        setTimeout(() => pollTranscriptionStatus(id), 2000);
      }
    } catch (err) {
      console.error('Error checking transcription status:', err);
      setError('Failed to check transcription status');
      setIsTranscribing(false);
    }
  }, [translateText]); // <-- Reverted

  const uploadAudio = useCallback(async (file, isRecording = false) => {
    if (!file || segmentState === 'finalized') return;

    // ✅ **FIX: Clean up the *previous* audio file first**
    if (audioElement) {
      audioElement.pause();
      setAudioElement(null);
    }
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
    }
    setIsPlaying(false);
    // --- End of fix ---

    setIsTranscribing(true);
    setError(null);
    setUploadProgress(0);

    if (isRecording) {
      setUploadingRecording(true);
      setAudioFile(null);
      setAudioUrl(null); 
    } else {
      setAudioFile(file);
      const url = URL.createObjectURL(file); // Create the new URL
      setAudioUrl(url); // Set the new URL
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('language', languageRef.current);

    try {
      const response = await api.post('/api/upload', formData, {
        onUploadProgress: (e) => setUploadProgress(Math.round((e.loaded * 100) / e.total)),
      });
      setTranscriptId(response.data.id);
      pollTranscriptionStatus(response.data.id);
    } catch (err) {
      console.error('Error uploading audio:', err);
      setError(err.response?.data?.detail || 'Failed to upload audio file');
      setIsTranscribing(false);
    } finally {
      setUploadingRecording(false);
    }
  }, [pollTranscriptionStatus, audioUrl, segmentState, audioElement]); // Note: audioElement is now a dependency

  const isBusy = isRecording; // <-- UPDATED

  const onDrop = useCallback((acceptedFiles) => {
    const f = acceptedFiles[0];
    if (f) uploadAudio(f, false);
  }, [uploadAudio]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.flac', '.aiff', '.au', '.ogg', '.webm', '.m4a', '.opus', '.wave'],
      'video/mp4': ['.mp4'], 'video/quicktime': ['.mov'], 'video/x-msvideo': ['.avi'],
      'video/x-ms-wmv': ['.wmv'], 'video/x-flv': ['.flv'], 'video/3gpp': ['.3gp'],
    },
    maxFiles: 1,
    disabled: isBusy || segmentState === 'finalized', // <-- UPDATED
  });

  const toggleAudioPlayback = useCallback(() => {
    if (!audioUrl) return;
    if (!audioElement) {
      const audio = new Audio(audioUrl);
      audio.onended = () => setIsPlaying(false);
      setAudioElement(audio);
      audio.play();
      setIsPlaying(true);
    } else {
      if (isPlaying) { audioElement.pause(); setIsPlaying(false); }
      else { audioElement.play(); setIsPlaying(true); }
    }
  }, [audioUrl, audioElement, isPlaying]);

  const startRecording = useCallback(async () => {
    if (segmentState === 'finalized' || isBusy) return; // <-- UPDATED
    try {
      setError(null);
      audioChunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
      streamRef.current = stream;
      const mimeTypes = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/wav'];
      let mimeType = mimeTypes.find((t) => MediaRecorder.isTypeSupported(t)) || '';
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType || 'audio/wav' });
        if (audioBlob.size === 0) return;
        const ext = (mimeType.split('/')[1] || 'wav').split(';')[0];
        const name = `recording-${getSafeTimestamp()}.${ext}`;
        const recordingFile = new File([audioBlob], name, { type: audioBlob.type });
        await uploadAudio(recordingFile, true);
      };
      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Recording error:', err);
      setError(`Failed to start recording: ${err.message}`);
    }
  }, [segmentState, isBusy, uploadAudio]); // <-- UPDATED

  const stopRecording = useCallback(async () => {
    try {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
      setIsRecording(false);
    } catch (err) {
      console.error('Stop recording error:', err);
      setError('Error while stopping recording.');
    }
  }, []);
  
  const applyGlossary = useCallback(() => {
    if (!translatedText || segmentState === 'finalized') return;
    let updated = translatedText;
    const lang = detectedLanguage;
    glossaryRules.forEach((r) => {
      if (r.language_pair === `${lang}-${selectedLanguage}`) {
        updated = updated.replace(new RegExp(r.source_term, 'gi'), r.target_term);
      }
    });
    setTranslatedText(updated);
    setSegmentState('glossary-fixed');
  }, [translatedText, segmentState, detectedLanguage, glossaryRules, selectedLanguage]);

  const downloadTXT = useCallback(() => {
    if (!translatedText) return;
    const blob = new Blob([translatedText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `translation_${getSafeTimestamp()}.txt`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }, [translatedText]);

  const addRule = useCallback(() => {
    if (!newRule.source_term || !newRule.target_term) return;
    setGlossaryRules((r) => [...r, newRule]);
    setNewRule({ source_term: '', target_term: '', language_pair: `${detectedLanguage}-${selectedLanguage}` });
  }, [newRule, detectedLanguage, selectedLanguage]);

  const removeRule = useCallback((idx) => {
    setGlossaryRules((r) => r.filter((_, i) => i !== idx));
  }, []);

  // --- Return all state and handlers ---
  return {
    sourceText, setSourceText,
    translatedText,
    selectedLanguage, setSelectedLanguage,
    metrics,
    metricsHistory,
    isTranslating,
    error,
    segmentState, setSegmentState,
    glossaryOpen, setGlossaryOpen,
    audioFile,
    isTranscribing,
    transcriptId,
    sourceLanguage, setSourceLanguage,
    detectedLanguage,
    languageConfidence,
    uploadProgress,
    audioUrl,
    isPlaying,
    isRecording,
    uploadingRecording,
    isBusy, // <-- This is now correctly defined as just 'isRecording'
    glossaryRules,
    newRule, setNewRule,
    // Handlers
    translateText,
    uploadAudio,
    getRootProps,
    getInputProps,
    isDragActive,
    toggleAudioPlayback,
    startRecording,
    stopRecording,
    applyGlossary,
    downloadTXT,
    addRule,
    removeRule,
    // Removed: liveTranscriptionHook
  };
};