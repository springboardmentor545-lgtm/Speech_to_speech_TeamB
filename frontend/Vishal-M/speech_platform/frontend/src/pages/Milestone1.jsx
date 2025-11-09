// src/pages/Milestone1.jsx
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

// Centralized utilities
import api from '../utils/api'; 
import { getSafeTimestamp } from '../utils/helpers'; 

// Page-specific components
import LanguageSelector from '../components/milestone1/LanguageSelector';
import UploadCard from '../components/milestone1/UploadCard';
import RecordingCard from '../components/milestone1/RecordingCard';
import TranscriptsTable from '../components/milestone1/TranscriptsTable';
import TranscriptModal from '../components/milestone1/TranscriptModal';

/* ---------------- component ---------------- */
const Milestone1 = () => {
  const [file, setFile] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState('auto');
  const [isRecording, setIsRecording] = useState(false);
  const [transcripts, setTranscripts] = useState([]);
  const [selectedTranscript, setSelectedTranscript] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [uploadingRecording, setUploadingRecording] = useState(false);

  // recording refs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef(null);
  const streamRef = useRef(null);

  // keep latest language for recording
  const languageRef = useRef(selectedLanguage);
  
  useEffect(() => { 
    languageRef.current = selectedLanguage; 
  }, [selectedLanguage]);

  // load existing transcripts + poll those in progress
  const fetchTranscripts = useCallback(async () => {
    try {
      const response = await api.get('/api/transcripts');
      const items = response.data || [];
      setTranscripts(items);
      items.forEach((t) => {
        if (t.status === 'processing' || t.status === 'queued') {
          pollTranscriptStatus(t.id);
        }
      });
    } catch (err) {
      console.error('Error fetching transcripts:', err);
      setError('Could not load existing transcripts.');
    }
  }, []);

  useEffect(() => { fetchTranscripts(); }, [fetchTranscripts]);

  const pollTranscriptStatus = useCallback((transcriptId) => {
    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/api/transcripts/${transcriptId}`);
        const transcript = response.data;
        if (transcript.status === 'completed' || transcript.status === 'failed') {
          clearInterval(interval);
          setTranscripts((prev) => prev.map((t) => (t.id === transcriptId ? transcript : t)));
        } else {
          setTranscripts((prev) =>
            prev.map((t) => (t.id === transcriptId ? { ...t, status: transcript.status } : t))
          );
        }
      } catch (err) {
        clearInterval(interval);
        console.error('Error polling transcript status:', err);
      }
    }, 2000);
  }, []);

  // upload function (used by drop + recording)
  const uploadAudio = useCallback(async (audioFile, fromRecording = false) => {
    setError(null);
    setUploadProgress(1);
    if (fromRecording) setUploadingRecording(true);
    else setFile(audioFile);

    const formData = new FormData();
    formData.append('file', audioFile);
    formData.append('language', languageRef.current);

    try {
      const response = await api.post('/api/upload', formData, {
        onUploadProgress: (evt) => {
          const pct = Math.round((evt.loaded * 100) / evt.total);
          setUploadProgress(pct);
        },
      });
      // push new transcript & start polling
      setTranscripts((prev) => [response.data, ...prev]);
      pollTranscriptStatus(response.data.id);
    } catch (err) {
      console.error('Error uploading file:', err);
      setError(err.response?.data?.detail || 'File upload failed.');
    } finally {
      setUploadProgress(0);
      setFile(null);
      setUploadingRecording(false);
    }
  }, [pollTranscriptStatus]);

  // dropzone
  const onDrop = useCallback(async (acceptedFiles) => {
    const f = acceptedFiles[0];
    if (f) uploadAudio(f, false);
  }, [uploadAudio]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.flac', '.aiff', '.au', '.ogg', '.webm', '.m4a', '.opus', '.wave'],
      'video/mp4': ['.mp4'],
      'video/quicktime': ['.mov'],
      'video/x-msvideo': ['.avi'],
      'video/x-ms-wmv': ['.wmv'],
      'video/x-flv': ['.flv'],
      'video/3gpp': ['.3gp'],
    },
    maxFiles: 1,
    disabled: isRecording, 
  });

  // recording start/stop
  const startRecording = async () => {
    try {
      setError(null);
      audioChunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
      });
      streamRef.current = stream;

      const mimeTypes = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/wav'];
      let mimeType = mimeTypes.find((t) => MediaRecorder.isTypeSupported(t)) || '';
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType || 'audio/wav' });
        if (audioBlob.size === 0) {
          console.warn('Empty recording, not uploading.');
          setUploadingRecording(false);
          return;
        }
        const ext = (mimeType.split('/')[1] || 'wav').split(';')[0];
        const safeTs = getSafeTimestamp();
        const recordingFile = new File([audioBlob], `recording-${safeTs}.${ext}`, { type: audioBlob.type });
        await uploadAudio(recordingFile, true);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Recording error:', err);
      setError(`Failed to start recording: ${err.message}`);
    }
  };

  const stopRecording = async () => {
    try {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
      setIsRecording(false);
    } catch (err) {
      console.error('Stop recording error:', err);
      setError('Error while stopping recording.');
    }
  };

  // CSV export
  const exportCSV = async () => {
    try {
      setError(null);
      const response = await api.get('/api/export/csv', { responseType: 'blob' });
      const blob = response.data;

      const header = response.headers.get('content-disposition');
      let filename = 'transcripts.csv';
      if (header) {
        const parts = header.split('filename=');
        if (parts.length === 2) filename = parts[1].replaceAll('"', '');
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.setAttribute('download', filename);
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exporting CSV:', err);
      setError('Failed to export CSV. Are there any transcripts?');
    }
  };
   
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Milestone 1: Speech Recognition & Data Collection</h1>
        <p className="text-gray-400">Upload audio files or record live speech for transcription</p>
      </div>

      {error && (
        <div className="p-4 bg-red-500/20 text-red-300 rounded-lg border border-red-500">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* ✅ **FIX 1:** LanguageSelector is moved here, *ABOVE* the grid. */}
      <LanguageSelector value={selectedLanguage} onChange={setSelectedLanguage} disabled={isRecording} />

      {/* ✅ **FIX 2:** The grid now contains UploadCard (left) and RecordingCard (right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      
        <UploadCard
          getRootProps={getRootProps}
          getInputProps={getInputProps}
          isRecording={isRecording} 
          isDragActive={isDragActive}
          file={file}
          uploadProgress={uploadProgress}
          uploadingRecording={uploadingRecording}
        />

        <RecordingCard
          isRecording={isRecording}
          stopRecording={stopRecording}
          startRecording={startRecording}
          uploadingRecording={uploadingRecording}
          uploadProgress={uploadProgress}
          disabled={isRecording} 
        />
      </div>

      <TranscriptsTable
        transcripts={transcripts}
        exportCSV={exportCSV}
        onSelectTranscript={setSelectedTranscript}
      />

      <TranscriptModal
        transcript={selectedTranscript}
        onClose={() => setSelectedTranscript(null)}
      />
    </div>
  );
};

export default Milestone1;