import { useEffect, useRef } from 'react'

export default function AudioVisualizer({ isActive, stream }) {
  const canvasRef = useRef(null)
  const animationFrameRef = useRef(null)
  const audioContextRef = useRef(null)
  const analyserRef = useRef(null)
  const sourceRef = useRef(null)

  useEffect(() => {
    if (isActive && stream) {
      // Initialize audio context and analyser only once or if needed
      if (!audioContextRef.current) {
        audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)()
        analyserRef.current = audioContextRef.current.createAnalyser()
        analyserRef.current.fftSize = 256 // Smaller FFT size for performance
      }

      const analyser = analyserRef.current
      const source = audioContextRef.current.createMediaStreamSource(stream)
      sourceRef.current = source // Keep track to disconnect later
      source.connect(analyser)

      const bufferLength = analyser.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)
      const canvas = canvasRef.current
      const ctx = canvas.getContext('2d')
      const WIDTH = canvas.width
      const HEIGHT = canvas.height

      const draw = () => {
        animationFrameRef.current = requestAnimationFrame(draw)
        analyser.getByteFrequencyData(dataArray)

        // Clear canvas with transparency
        ctx.fillStyle = 'rgba(17, 24, 39, 0.5)' // Slightly transparent background
        ctx.fillRect(0, 0, WIDTH, HEIGHT)

        const barWidth = (WIDTH / bufferLength) * 1.5 // Make bars slightly thinner
        let x = 0

        for (let i = 0; i < bufferLength; i++) {
          const barHeight = (dataArray[i] / 255) * HEIGHT * 0.7 // Scale height

          // Create gradient for each bar - can be optimized if performance is an issue
          const gradient = ctx.createLinearGradient(0, HEIGHT - barHeight, 0, HEIGHT)
          gradient.addColorStop(0, 'rgb(79, 70, 229)') // primary-600
          gradient.addColorStop(1, 'rgb(129, 140, 248)') // primary-400

          ctx.fillStyle = gradient
          ctx.fillRect(x, HEIGHT - barHeight, barWidth, barHeight)

          x += barWidth + 2 // Increase spacing between bars
        }
      }
      draw()

    } else {
      // Cleanup when not active or stream is removed
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (sourceRef.current) {
        sourceRef.current.disconnect() // Disconnect the source node
        sourceRef.current = null
      }
      // Optionally close the audio context if you know it won't be reused soon
      // if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      //   audioContextRef.current.close().then(() => audioContextRef.current = null);
      // }

      // Clear the canvas when inactive
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = 'rgb(17, 24, 39)'; // Dark background
        ctx.fillRect(0, 0, canvas.width, canvas.height);
      }
    }

    // Cleanup function for when the component unmounts
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (sourceRef.current) {
        sourceRef.current.disconnect()
      }
       if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
         audioContextRef.current.close().catch(e => console.error("Error closing AudioContext:", e));
         audioContextRef.current = null;
       }
    }
  }, [isActive, stream])

  return (
    <div className="w-full max-w-xl mx-auto">
      <canvas
        ref={canvasRef}
        width={600} // Base width
        height={100} // Base height
        className="w-full h-auto rounded-lg glass-panel" // Responsive width, auto height
      />
    </div>
  )
}
