import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Upload, Mic, MicOff, Download, CheckCircle, AlertCircle, Clock, FileText, Languages } from 'lucide-react';
import { useDropzone } from 'react-dropzone';

// Self-contained API helper
const api = {
  get: async (url, config = {}) => {
    const backendUrl = "http://localhost:8000";
    const response = await fetch(`${backendUrl}${url}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        ...config.headers,
      },
      ...config,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw { response: { data: errorData } };
    }

    if (config.responseType === 'blob') {
      return {
        data: await response.blob(),
        headers: response.headers,
      };
    }
    
    return { data: await response.json() };
  },
  
  post: (url, data, config = {}) => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const backendUrl = "http://localhost:8000";
      xhr.open('POST', `${backendUrl}${url}`, true);

      if (config.headers) {
        Object.entries(config.headers).forEach(([key, value]) => {
          xhr.setRequestHeader(key, value);
        });
      }
      
      const isFormData = data instanceof FormData;
      if (!isFormData) {
         xhr.setRequestHeader('Content-Type', 'application/json');
         xhr.setRequestHeader('Accept', 'application/json');
      }

      if (config.onUploadProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            config.onUploadProgress(event);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve({ data: JSON.parse(xhr.responseText) });
        } else {
          let errorData;
          try {
            errorData = JSON.parse(xhr.responseText);
          } catch (e) {
            errorData = { detail: xhr.statusText };
          }
          reject({ response: { data: errorData } });
        }
      };

      xhr.onerror = () => {
        reject({ response: { data: { detail: 'Network error' } } });
      };

      const body = isFormData ? data : JSON.stringify(data);
      xhr.send(body);
    });
  },
};


const LanguageSelector = ({ value, onChange, disabled }) => (
  <div className="flex items-center space-x-2 bg-gray-700/50 p-3 rounded-lg border border-gray-700">
    <Languages size={20} className="text-primary-400" />
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className="bg-gray-800 text-white focus:outline-none w-full disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <option value="auto">Auto-Detect Language</option>
      <option value="en-US">English (US)</option>
      <option value="en-IN">English (India)</option>
      <option value="hi-IN">Hindi (India)</option>
      <option value="ta-IN">Tamil (India)</option>
      <option value="te-IN">Telugu (India)</option>
      <option value="es-ES">Spanish (Spain)</option>
      <option value="fr-FR">French (France)</option>
      <option value="de-DE">German (Germany)</option>
    </select>
  </div>
);

// Helper function to create a filename-safe timestamp
const getSafeTimestamp = () => {
  const date = new Date();
  const Y = date.getFullYear();
  const M = String(date.getMonth() + 1).padStart(2, '0');
  const D = String(date.getDate()).padStart(2, '0');
  const h = String(date.getHours()).padStart(2, '0');
  const m = String(date.getMinutes()).padStart(2, '0');
  const s = String(date.getSeconds()).padStart(2, '0');
  return `${Y}${M}${D}_${h}${m}${s}`;
};

const Milestone1 = () => {
  const [file, setFile] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState('auto');
  const [isRecording, setIsRecording] = useState(false);
  const [transcripts, setTranscripts] = useState([]);
  const [selectedTranscript, setSelectedTranscript] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const [uploadingRecording, setUploadingRecording] = useState(false);


  // Refs for recording
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const streamRef = useRef(null);
  
  // Ref to track language for recording
  const languageRef = useRef(selectedLanguage);
  useEffect(() => {
    languageRef.current = selectedLanguage;
  }, [selectedLanguage]);

  const fetchTranscripts = useCallback(async () => {
    try {
      const response = await api.get('/api/transcripts');
      const fetchedTranscripts = response.data || [];
      setTranscripts(fetchedTranscripts);
      fetchedTranscripts.forEach(t => {
        if (t.status === 'processing' || t.status === 'queued') {
          pollTranscriptStatus(t.id);
        }
      });
    } catch (err) {
      console.error('Error fetching transcripts:', err);
      setError('Could not load existing transcripts.');
    }
  }, []);

  const pollTranscriptStatus = useCallback((transcriptId) => {
    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/api/transcripts/${transcriptId}`);
        const transcript = response.data;
        if (transcript.status === 'completed' || transcript.status === 'failed') {
          clearInterval(interval);
          setTranscripts(prev =>
            prev.map(t => (t.id === transcriptId ? transcript : t))
          );
        } else {
          setTranscripts(prev =>
            prev.map(t => (t.id === transcriptId ? { ...t, status: transcript.status } : t))
          );
        }
      } catch (err) {
        clearInterval(interval);
        console.error('Error polling transcript status:', err);
      }
    }, 2000);
  }, []);
  
  useEffect(() => {
    fetchTranscripts();
  }, [fetchTranscripts]);

  // Unified upload function
  const uploadAudio = useCallback(async (audioFile, isRecording = false) => {
    setError(null);
    setUploadProgress(1);
    if (isRecording) {
      setUploadingRecording(true);
    } else {
      setFile(audioFile);
    }

    const formData = new FormData();
    formData.append('file', audioFile);
    formData.append('language', languageRef.current);

    try {
      const response = await api.post('/api/upload', formData, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        },
      });
      
      setTranscripts(prev => [response.data, ...prev]);
      pollTranscriptStatus(response.data.id);

    } catch (err)
 {
      console.error('Error uploading file:', err);
      setError(err.response?.data?.detail || 'File upload failed.');
    } finally {
      setUploadProgress(0);
      setFile(null);
      setUploadingRecording(false);
    }
  }, [pollTranscriptStatus]);


  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      uploadAudio(file, false);
    }
  }, [uploadAudio]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.webm']
    },
    maxFiles: 1,
    disabled: isRecording
  });

  const startRecording = async () => {
    try {
      setError(null);
      audioChunksRef.current = [];

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        }
      });
      
      streamRef.current = stream;
      
      // Determine a suitable MIME type
      const mimeTypes = [
        'audio/webm;codecs=opus',
        'audio/ogg;codecs=opus',
        'audio/wav'
      ];
      let mimeType = mimeTypes.find(type => MediaRecorder.isTypeSupported(type));
      if (!mimeType) {
        console.warn("No preferred MIME type supported, using default.");
        mimeType = ''; // Let the browser decide
      }

      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: mimeType });

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        // Recording stopped, create Blob and upload
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType || 'audio/wav' });
        const fileExtension = (mimeType.split('/')[1] || 'wav').split(';')[0];
        
        // --- FIX: Use a safe timestamp for the filename ---
        const safeTimestamp = getSafeTimestamp();
        const recordingFile = new File([audioBlob], `recording-${safeTimestamp}.${fileExtension}`, {
          type: audioBlob.type,
        });
        // --- END FIX ---
        
        // Upload the recorded file
        await uploadAudio(recordingFile, true);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);

    } catch (error) {
      console.error("❌ Recording error:", error);
      setError(`Failed to start recording: ${error.message}`);
    }
  };

  const stopRecording = async () => {
    try {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop(); // This will trigger the 'onstop' event
      }

      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }

      setIsRecording(false);
      console.log('✅ Recording stopped, preparing upload...');
      
    } catch (error) {
      console.error('❌ Stop recording error:', error);
      setError('Error while stopping recording.');
    }
  };

  const exportCSV = async () => {
    try {
      setError(null);
      const response = await api.get('/api/export/csv', { responseType: 'blob' });
      const blob = response.data;
      
      const header = response.headers.get('content-disposition');
      let filename = 'transcripts.csv';
      if (header) {
        const parts = header.split('filename=');
        if (parts.length === 2) {
          filename = parts[1].replaceAll('"', '');
        }
      }

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

    } catch (err) {
      console.error('Error exporting CSV:', err);
      setError('Failed to export CSV. Are there any transcripts?');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={16} className="text-green-500" />;
      case 'processing':
        return <Clock size={16} className="text-yellow-500 animate-spin" />;
      case 'failed':
        return <AlertCircle size={16} className="text-red-500" />;
      case 'queued':
        return <Clock size={16} className="text-gray-500" />;
      default:
        return <FileText size={16} className="text-gray-500" />;
    }
  };

  const displayLanguage = (transcript) => {
    if (transcript.status === 'processing' || transcript.status === 'queued') {
      return <span className="text-gray-400 italic">Detecting...</span>;
    }
    // Handle potential error message in language field if detection failed
    if (transcript.language && transcript.language.startsWith('unknown')) {
       return <span className="text-yellow-400 italic">Auto-Detect</span>;
    }
    return transcript.language;
  };
  

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Milestone 1: Speech Recognition & Data Collection</h1>
        <p className="text-gray-400">Upload audio files or record live speech for transcription</p>
      </div>

      {error && (
        <div className="p-4 bg-red-500/20 text-red-300 rounded-lg border border-red-500">
          <strong>Error:</strong> {error}
        </div>
      )}

      <LanguageSelector value={selectedLanguage} onChange={setSelectedLanguage} disabled={isRecording} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upload Section */}
        <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
          <h2 className="text-lg font-semibold mb-4 text-white">Upload Audio File</h2>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
              isRecording 
                ? 'border-gray-700 bg-gray-800/50 cursor-not-allowed opacity-50'
                : isDragActive 
                  ? 'border-primary-500 bg-primary-500/10' 
                  : 'border-gray-600 hover:border-gray-500 cursor-pointer'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="mx-auto mb-2 text-gray-400" size={32} />
            <p className="text-gray-400">
              {isRecording 
                ? 'Stop recording to upload a file'
                : isDragActive 
                  ? 'Drop the audio file here' 
                  : 'Drag & drop an audio file here, or click to select'
              }
            </p>
            <p className="text-sm text-gray-500 mt-1">Supports: MP3, WAV, M4A, FLAC, AAC, OGG, WEBM</p>
          </div>

          {(file || uploadProgress > 0) && !uploadingRecording && (
            <div className="mt-4 p-4 bg-gray-700/50 rounded-lg">
              <p className="text-sm text-gray-300 truncate">Selected: {file?.name}</p>
              {uploadProgress > 0 && (
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>{uploadProgress < 100 ? 'Uploading...' : 'Processing...'}</span>
                    <span>{uploadProgress < 100 ? `${uploadProgress}%` : ''}</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${uploadProgress < 100 ? 'bg-primary-600' : 'bg-primary-600 animate-pulse'}`}
                      style={{ width: `${uploadProgress < 100 ? uploadProgress : 100}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Recording Section */}
        <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
          <h2 className="text-lg font-semibold mb-4 text-white">Live Recording</h2>
          <div className="flex flex-col items-center space-y-4">
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={uploadingRecording}
              className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-colors w-48 justify-center ${
                isRecording
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-primary-600 hover:bg-primary-700 text-white'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
              <span>{isRecording ? 'Stop Recording' : 'Start Recording'}</span>
            </button>
            {isRecording && (
              <div className="flex items-center space-x-2 text-red-400">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                <span className="text-sm">Recording...</span>
              </div>
            )}
             {uploadingRecording && (
              <div className="mt-4 p-4 bg-gray-700/50 rounded-lg w-full">
                <p className="text-sm text-gray-300 truncate">Uploading recording...</p>
                {uploadProgress > 0 && (
                  <div className="mt-3">
                    <div className="flex justify-between text-xs text-gray-400 mb-1">
                      <span>{uploadProgress < 100 ? 'Uploading...' : 'Processing...'}</span>
                      <span>{uploadProgress < 100 ? `${uploadProgress}%` : ''}</span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all duration-300 ${uploadProgress < 100 ? 'bg-primary-600' : 'bg-primary-600 animate-pulse'}`}
                        style={{ width: `${uploadProgress < 100 ? uploadProgress : 100}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Transcripts Table */}
      {transcripts.length > 0 && (
        <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-white">Transcripts</h2>
            <button
              onClick={exportCSV}
              className="flex items-center space-x-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded-lg text-white transition-colors"
            >
              <Download size={16} />
              <span>Export CSV</span>
            </button>
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
                {transcripts.map((transcript) => (
                  <tr key={transcript.id} className="border-b border-gray-700 hover:bg-gray-700/50">
                    <td className="py-3 px-4 text-gray-300">{transcript.id}</td>
                    <td className="py-3 px-4 text-gray-300 truncate max-w-xs">{transcript.filename}</td>
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(transcript.status)}
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          transcript.status === 'completed' 
                            ? 'bg-green-500/20 text-green-400' 
                            : (transcript.status === 'processing' || transcript.status === 'queued')
                              ? 'bg-yellow-500/20 text-yellow-400'
                              : 'bg-red-500/20 text-red-400'
                        }`}>
                          {transcript.status}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-gray-300">{displayLanguage(transcript)}</td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => setSelectedTranscript(transcript)}
                        className="text-primary-400 hover:text-primary-300 mr-3 disabled:text-gray-500 disabled:cursor-not-allowed"
                        disabled={transcript.status !== 'completed'}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Transcript Modal */}
      {selectedTranscript && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedTranscript(null)}>
          <div className="bg-gray-800 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
            <div className="p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-white truncate pr-4">{selectedTranscript.filename}</h3>
                <button
                  onClick={() => setSelectedTranscript(null)}
                  className="text-gray-400 hover:text-white text-3xl leading-none"
                >
                  &times;
                </button>
              </div>
              <div className="bg-gray-700/50 p-4 rounded-lg">
                <p className="text-gray-300 whitespace-pre-wrap">
                  {selectedTranscript.text || "No text available."}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Milestone1;