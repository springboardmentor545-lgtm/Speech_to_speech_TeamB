import { useState, useCallback, useEffect } from 'react'
import FileUploader from '../components/FileUploader'
import TranscriptTable from '../components/TranscriptTable'
import { Download } from 'lucide-react'

export default function BatchTranscription() {
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  const handleUploadComplete = useCallback(() => {
    setRefreshTrigger(prev => prev + 1)
  }, [])

  const handleExportCSV = () => {
    window.open('/api/export/csv', '_blank')
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Batch Transcription</h1>
          <p className="mt-2 text-gray-400">
            Upload audio files for asynchronous processing
          </p>
        </div>
        <button
          onClick={handleExportCSV}
          className="btn-secondary flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          Export All
        </button>
      </div>

      <FileUploader onUploadComplete={handleUploadComplete} />
      <TranscriptTable refreshTrigger={refreshTrigger} />
    </div>
  )
}
