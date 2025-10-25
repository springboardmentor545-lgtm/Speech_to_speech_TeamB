import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, X, CheckCircle, AlertCircle, Loader } from 'lucide-react'
import axios from 'axios'

export default function FileUploader({ onUploadComplete }) {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState(null) // { type: 'success' | 'error', message: string }

  const onDrop = useCallback((acceptedFiles) => {
    // Only take the first file if multiple are dropped
    setFiles(acceptedFiles.slice(0, 1))
    setUploadStatus(null)
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm']
    },
    multiple: false // Ensure only one file can be selected
  })

  const handleUpload = async () => {
    if (files.length === 0) return

    setUploading(true)
    setUploadStatus(null)

    const formData = new FormData()
    formData.append('file', files[0])

    try {
      const response = await axios.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      setUploadStatus({
        type: 'success',
        message: `File "${files[0].name}" uploaded. Processing started (ID: ${response.data.id}).`
      })
      setFiles([]) // Clear file list on success

      // Notify parent after a short delay to allow backend processing start
      setTimeout(() => {
        onUploadComplete?.()
      }, 1500) // Increased delay

    } catch (error) {
      setUploadStatus({
        type: 'error',
        message: error.response?.data?.detail || 'Upload failed. Please try again.'
      })
      console.error("Upload error:", error.response?.data || error.message)
    } finally {
      setUploading(false)
    }
  }

  const removeFile = () => {
    setFiles([])
    setUploadStatus(null)
  }

  return (
    <div className="glass-panel p-6 space-y-4">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-all duration-300 cursor-pointer ${
          isDragActive
            ? 'border-primary-500 bg-primary-900/20 scale-105'
            : 'border-gray-700 hover:border-gray-600 hover:bg-gray-800/30'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <p className="text-lg font-medium text-white mb-2">
          {isDragActive ? 'Drop audio file here' : 'Drag & drop single audio file'}
        </p>
        <p className="text-sm text-gray-400">
          or click to browse (Max 50MB: WAV, MP3, M4A, OGG, FLAC, WEBM)
        </p>
      </div>

      {files.length > 0 && (
        <div className="space-y-3 animate-fade-in">
          <div className="flex items-center justify-between glass-panel p-4">
            <div className="flex items-center gap-3 overflow-hidden">
              <File className="w-5 h-5 text-primary-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{files[0].name}</p>
                <p className="text-xs text-gray-400">
                  {(files[0].size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button
              onClick={removeFile}
              className="text-gray-400 hover:text-white transition-colors flex-shrink-0 ml-2"
              aria-label="Remove file"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <button
            onClick={handleUpload}
            disabled={uploading}
            className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {uploading ? (
                <>
                  <Loader className="w-5 h-5 animate-spin" /> Uploading...
                </>
            ) : 'Upload & Process'}
          </button>
        </div>
      )}

      {uploadStatus && (
        <div
          className={`glass-panel p-4 flex items-center gap-3 animate-fade-in ${
            uploadStatus.type === 'success'
              ? 'border-green-500/50 bg-green-900/20'
              : 'border-red-500/50 bg-red-900/20'
          }`}
        >
          {uploadStatus.type === 'success' ? (
            <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
          )}
          <p className={`text-sm ${uploadStatus.type === 'success' ? 'text-green-400' : 'text-red-400'}`}>
            {uploadStatus.message}
          </p>
        </div>
      )}
    </div>
  )
}
