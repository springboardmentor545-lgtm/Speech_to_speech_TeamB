import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Play, Pause, Volume2, RefreshCw, Zap, Clock, AlertTriangle } from "lucide-react";

const Milestone3 = () => {
  const [text, setText] = useState("");
  const [audioUrl, setAudioUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState(null);
  const [latency, setLatency] = useState(0);
  const [drift, setDrift] = useState(0);
  const [circuitBreaker, setCircuitBreaker] = useState(false);
  const audioRef = useRef(null);

  // Load last translated text from Milestone 2
  useEffect(() => {
    const lastTranslated = localStorage.getItem("lastTranslatedText");
    if (lastTranslated) {
      setText(lastTranslated);
    }
  }, []);

  // Auto-reset circuit breaker on playback end
  const handleAudioEnded = () => {
    setIsPlaying(false);
  };

  // Generate Speech
  const handleTTS = async () => {
    if (!text.trim()) {
      alert("Please enter or import text for speech synthesis.");
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const startTime = performance.now();
      const response = await axios.post(
        "http://127.0.0.1:8000/api/tts",
        { text, target_language: "en-US" },
        { responseType: "blob" }
      );
      const endTime = performance.now();

      setLatency(Math.round(endTime - startTime));

      const blob = new Blob([response.data], { type: "audio/wav" });
      const url = window.URL.createObjectURL(blob);
      setAudioUrl(url);
      setDrift(0);
      setIsLoading(false);
    } catch (err) {
      console.error("TTS error:", err);
      setError("TTS generation failed. Check backend or Azure configuration.");
      setIsLoading(false);
    }
  };

  // Playback controls
  const togglePlayback = () => {
    if (!audioUrl) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play();
      setIsPlaying(true);
    }
  };

  // Circuit Breaker
  const toggleCircuitBreaker = () => setCircuitBreaker(!circuitBreaker);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Milestone 3: Speech-to-Speech Conversion</h1>
        <p className="text-gray-400">
          Generate and play speech audio from translated text (Milestone 2 output).
        </p>
      </div>

      {error && (
        <div className="p-4 bg-red-500/20 text-red-300 rounded-lg border border-red-500">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Input Area */}
      <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Input Text (from Translation or Custom)
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="w-full h-40 p-3 bg-gray-700 border border-gray-600 rounded-lg text-white resize-none"
          placeholder="Enter or paste text to synthesize..."
        />
        <div className="flex items-center space-x-3 mt-4">
          <button
            onClick={handleTTS}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium"
          >
            {isLoading ? "Generating..." : "Generate Speech"}
          </button>

          <button
            onClick={() => {
              setText("");
              setAudioUrl("");
              setError(null);
              setLatency(0);
            }}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-white font-medium flex items-center space-x-2"
          >
            <RefreshCw size={16} />
            <span>Reset</span>
          </button>
        </div>
      </div>

      {/* Audio Player */}
      {audioUrl && (
        <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
          <h2 className="text-lg font-semibold mb-4 text-white">Audio Playback</h2>
          <audio
            ref={audioRef}
            src={audioUrl}
            onEnded={handleAudioEnded}
            className="hidden"
          />
          <div className="flex flex-col items-center space-y-4">
            <button
              onClick={togglePlayback}
              className={`flex items-center space-x-2 px-6 py-3 rounded-lg font-medium transition-colors ${
                isPlaying
                  ? "bg-red-600 hover:bg-red-700 text-white"
                  : "bg-green-600 hover:bg-green-700 text-white"
              }`}
            >
              {isPlaying ? <Pause size={18} /> : <Play size={18} />}
              <span>{isPlaying ? "Pause Audio" : "Play Audio"}</span>
            </button>

            <div className="flex items-center space-x-2">
              <Volume2 size={20} className="text-primary-400" />
              <span className="text-gray-300">
                {isPlaying ? "Playing speech output..." : "Ready to play"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* System Stats */}
      <div className="bg-gray-800/50 backdrop-blur-lg rounded-xl p-6 border border-gray-700">
        <h2 className="text-lg font-semibold mb-4 text-white">System Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-700/50 p-4 rounded-lg text-center">
            <Zap size={20} className="mx-auto text-yellow-400 mb-2" />
            <div className="text-sm text-gray-400">Latency</div>
            <div className="text-lg font-semibold text-yellow-400">{latency} ms</div>
          </div>
          <div className="bg-gray-700/50 p-4 rounded-lg text-center">
            <Clock size={20} className="mx-auto text-blue-400 mb-2" />
            <div className="text-sm text-gray-400">Drift</div>
            <div className="text-lg font-semibold text-blue-400">{drift} ms</div>
          </div>
          <div className="bg-gray-700/50 p-4 rounded-lg text-center">
            <AlertTriangle size={20} className="mx-auto text-red-400 mb-2" />
            <div className="text-sm text-gray-400">Circuit Breaker</div>
            <div className="text-lg font-semibold">
              {circuitBreaker ? (
                <span className="text-yellow-400">Active</span>
              ) : (
                <span className="text-green-400">Normal</span>
              )}
            </div>
            <button
              onClick={toggleCircuitBreaker}
              className="mt-2 px-3 py-1 bg-gray-600 text-xs rounded text-gray-200 hover:bg-gray-500"
            >
              Toggle
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Milestone3;
