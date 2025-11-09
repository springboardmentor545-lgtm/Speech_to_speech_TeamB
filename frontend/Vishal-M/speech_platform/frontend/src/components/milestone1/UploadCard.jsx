// src/components/milestone1/UploadCard.jsx
import React from 'react';
import { Upload } from 'lucide-react';
import GlassCard from '../ui/GlassCard';

export default function UploadCard({
  getRootProps,
  getInputProps,
  isRecording,
  isDragActive,
  file,
  uploadProgress,
  uploadingRecording,
}) {
  return (
    <GlassCard>
      <h2 className="text-lg font-semibold mb-4">Upload Audio File</h2>
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isRecording
            ? 'border-gray-700 bg-gray-800/50 cursor-not-allowed opacity-50'
            : isDragActive
            ? 'border-indigo-500 bg-indigo-500/10'
            : 'border-gray-700 hover:border-gray-500 cursor-pointer'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="mx-auto mb-2 text-gray-400" size={32} />
        <p className="text-gray-400">
          {isRecording
            ? 'Stop recording to upload a file'
            : isDragActive
            ? 'Drop the audio file here'
            : 'Drag & drop an audio file here, or click to select'}
        </p>
        <p className="text-sm text-gray-500 mt-1">
          MP3, WAV, FLAC, M4A, MP4, MOV, AVI, WebM, OGG, etc.
        </p>
      </div>

      {(file || (uploadProgress > 0 && !uploadingRecording)) && (
        <div className="mt-4 p-4 bg-gray-800/60 rounded-lg border border-gray-700">
          <p className="text-sm text-gray-300 truncate">
            {file ? file.name : 'Uploading...'}
          </p>
          {uploadProgress > 0 && (
            <div className="mt-3">
              <div className="flex justify-between text-xs text-gray-400 mb-1">
                <span>{uploadProgress < 100 ? 'Uploading...' : 'Processing...'}</span>
                <span>{uploadProgress < 100 ? `${uploadProgress}%` : ''}</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all duration-300 ${
                    uploadProgress < 100 ? 'bg-indigo-500' : 'bg-indigo-500 animate-pulse'
                  }`}
                  style={{ width: `${uploadProgress < 100 ? uploadProgress : 100}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}
    </GlassCard>
  );
}