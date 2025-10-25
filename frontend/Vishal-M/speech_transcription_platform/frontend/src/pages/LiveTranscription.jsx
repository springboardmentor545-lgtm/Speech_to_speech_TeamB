import { useState, useRef, useEffect } from 'react'
import { Mic, Square, Loader } from 'lucide-react'
import AudioVisualizer from '../components/AudioVisualizer'

const WS_BASE_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`

export default function LiveTranscription() {
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [transcript, setTranscript] = useState([])
  const [currentLanguage, setCurrentLanguage] = useState(null)
  const [error, setError] = useState(null)

  const wsRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const streamRef = useRef(null)

  const startRecording = async () => {
    try {
      setError(null)
      setTranscript([])
      setIsProcessing(true)

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000
        }
      })
      streamRef.current = stream

      wsRef.current = new WebSocket(`${WS_BASE_URL}/ws/recognize-continuous`)

      wsRef.current.onopen = () => {
        setIsRecording(true)
        setIsProcessing(false)
      }

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.text) {
          setTranscript(prev => [...prev, {
            text: data.text,
            language: data.language,
            timestamp: new Date().toISOString()
          }])
          setCurrentLanguage(data.language)
        }
        if (data.status === 'error') {
          setError(data.error)
        }
      }

      wsRef.current.onerror = () => {
        setError('WebSocket connection error')
        stopRecording()
      }

      wsRef.current.onclose = () => {
        setIsRecording(false)
      }

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus' // Use a common, efficient codec
      })
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(event.data)
        }
      }

      mediaRecorder.start(250) // Send data more frequently for lower latency

    } catch (err) {
      setError(`Microphone access denied: ${err.message}`)
      setIsProcessing(false)
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current?.state === 'recording') {
      mediaRecorderRef.current.stop()
    }

    streamRef.current?.getTracks().forEach(track => track.stop())

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.close()
    }

    setIsRecording(false)
    setIsProcessing(false)
  }

  useEffect(() => {
    // Cleanup function runs on component unmount
    return () => {
      stopRecording()
    }
  }, [])

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-white">Live Transcription</h1>
        <p className="mt-2 text-gray-400">
          Real-time speech recognition with continuous streaming
        </p>
      </div>

      <div className="glass-panel p-8">
        <div className="flex flex-col items-center gap-6">
          <AudioVisualizer isActive={isRecording} stream={streamRef.current} />

          <div className="flex gap-4">
            {!isRecording ? (
              <button
                onClick={startRecording}
                disabled={isProcessing}
                className="btn-primary flex items-center gap-2 px-8 py-4 text-lg"
              >
                {isProcessing ? (
                  <>
                    <Loader className="w-6 h-6 animate-spin" />
                    Initializing...
                  </>
                ) : (
                  <>
                    <Mic className="w-6 h-6" />
                    Start Recording
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={stopRecording}
                className="px-8 py-4 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-all shadow-lg hover:shadow-red-500/50 flex items-center gap-2 text-lg animate-pulse-glow"
              >
                <Square className="w-6 h-6" />
                Stop Recording
              </button>
            )}
          </div>

          {currentLanguage && (
            <div className="glass-panel px-4 py-2 border border-primary-500/30">
              <span className="text-sm text-gray-400">Detected Language:</span>
              <span className="ml-2 text-primary-400 font-semibold">{currentLanguage}</span>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="glass-panel border-red-500/50 bg-red-900/20 p-4">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      <div className="glass-panel p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Transcript</h2>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {transcript.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              {isRecording ? 'Listening...' : 'Start recording to see transcript'}
            </p>
          ) : (
            transcript.map((item, index) => (
              <div
                key={index}
                className="glass-panel p-4 border-l-4 border-primary-500 animate-slide-in"
              >
                <p className="text-gray-200">{item.text}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                  <span>{item.language}</span>
                  <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
