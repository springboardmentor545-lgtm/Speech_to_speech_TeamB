// src/hooks/useLiveTranscription.js
import { useState, useRef, useCallback, useEffect } from 'react';
import TranscriptionSocket from '../utils/ws'; // Your WebSocket class

export const useLiveTranscription = (language = 'auto') => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [error, setError] = useState(null);

  const socketRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const languageRef = useRef(language);

  // Update language ref when prop changes
  useEffect(() => {
    languageRef.current = language;
  }, [language]);

  // This function is called when the WebSocket sends us a message
  const handleSocketMessage = (payload) => {
    // You may need to adjust this based on your backend's JSON structure
    // Assumes { "transcript": "..." } or { "text": "..." }
    const transcript = payload.transcript || payload.text;
    if (typeof transcript === 'string') {
      setLiveTranscript(transcript);
    }
  };

  const startStreaming = async () => {
    if (isStreaming) return;
    setError(null);
    setLiveTranscript('');
    
    try {
      // 1. Get Microphone Stream
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true },
      });
      streamRef.current = stream;

      // 2. Connect WebSocket
      socketRef.current = new TranscriptionSocket(languageRef.current);
      socketRef.current.onMessage = handleSocketMessage;
      socketRef.current.onError = (err) => setError('WebSocket connection error. Is the server running?');
      socketRef.current.onClose = () => console.log('WS closed');
      socketRef.current.connect();
      
      // Wait for WS to be open
      await new Promise((resolve, reject) => {
        socketRef.current.onOpen = resolve;
        socketRef.current.onError = (err) => reject(err); // Propagate error
      });

      // 3. Start MediaRecorder to stream chunks
      const mimeTypes = ['audio/webm;codecs=opus', 'audio/ogg;codecs=opus', 'audio/wav'];
      const mimeType = mimeTypes.find(MediaRecorder.isTypeSupported) || '';
      
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType });

      // 4. Send audio chunks to WebSocket as they become available
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0 && socketRef.current) {
          socketRef.current.sendBinary(event.data);
        }
      };

      // We send data in small chunks (e.g., every 500ms)
      mediaRecorderRef.current.start(500); 
      setIsStreaming(true);

    } catch (err) {
      console.error('Streaming error:', err);
      setError('Failed to start streaming: ' + (err.message || 'Check permissions.'));
    }
  };

  const stopStreaming = useCallback(() => {
    if (!isStreaming) return;

    // 1. Stop MediaRecorder
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
    }
    
    // 2. Stop Microphone
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
    }

    // 3. Close WebSocket
    if (socketRef.current) {
      socketRef.current.close();
    }
    
    mediaRecorderRef.current = null;
    streamRef.current = null;
    socketRef.current = null;
    setIsStreaming(false);

    // We keep the final transcript in the box, so we don't clear it here.
  }, [isStreaming]);
  
  // Return everything the UI needs
  return {
    isStreaming,
    liveTranscript,
    setLiveTranscript, // Allow parent to clear it
    error,
    startStreaming,
    stopStreaming,
  };
};