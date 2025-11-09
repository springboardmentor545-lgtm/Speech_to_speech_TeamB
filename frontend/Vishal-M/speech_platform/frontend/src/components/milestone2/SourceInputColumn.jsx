// src/components/milestone2/SourceInputColumn.jsx
import React, { useState } from 'react';
import {
  Upload, FileAudio, Play, Pause, Mic, MicOff, Download, ChevronDown, ChevronRight, Info
} from 'lucide-react';
import GlassCard from '../ui/GlassCard';
import PrimaryButton from '../ui/PrimaryButton';
import SectionTitle from '../ui/SectionTitle';
import Tag from '../ui/Tag';

// Glossary Drawer Component (nested for co-location)
function GlossaryDrawer({
  isOpen,
  onToggle,
  rules,
  newRule,
  onRuleChange,
  onAddRule,
  onRemoveRule,
  onApplyGlossary,
  detectedLanguage,
  selectedLanguage,
  segmentState,
  translatedText,
}) {
  return (
    <div className="rounded-lg border border-gray-700 overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-4 py-2 bg-gray-800/60 hover:bg-gray-800 flex items-center justify-between"
      >
        <span className="font-medium text-gray-200 flex items-center gap-2">
          {isOpen ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
          Glossary Rules & Settings
        </span>
        <Tag color="purple">Advanced</Tag>
      </button>

      {isOpen && (
        <div className="p-4 bg-gray-900/40">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            <input
              value={newRule.source_term}
              onChange={(e) => onRuleChange({ ...newRule, source_term: e.target.value })}
              placeholder="source term"
              className="p-2 bg-gray-800 border border-gray-700 rounded text-sm"
              disabled={segmentState === 'finalized'}
            />
            <input
              value={newRule.target_term}
              onChange={(e) => onRuleChange({ ...newRule, target_term: e.target.value })}
              placeholder="target term"
              className="p-2 bg-gray-800 border border-gray-700 rounded text-sm"
              disabled={segmentState === 'finalized'}
            />
            <input
              value={newRule.language_pair}
              onChange={(e) => onRuleChange({ ...newRule, language_pair: e.target.value })}
              placeholder="en-es"
              className="p-2 bg-gray-800 border border-gray-700 rounded text-sm"
              disabled={segmentState === 'finalized'}
            />
          </div>
          <div className="flex gap-2 mt-2">
            <PrimaryButton onClick={onAddRule} disabled={segmentState === 'finalized'}>Add Rule</PrimaryButton>
            <button
              onClick={onApplyGlossary}
              disabled={!translatedText || segmentState === 'finalized'}
              className="px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-gray-300 hover:bg-gray-700"
            >
              Apply Glossary
            </button>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            {rules
              .filter((r) => r.language_pair === `${detectedLanguage}-${selectedLanguage}`)
              .map((rule, i) => (
                <span key={i} className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded text-xs flex items-center gap-2">
                  {rule.source_term} → {rule.target_term} <button onClick={() => onRemoveRule(i)} className="text-gray-400 hover:text-white">×</button>
                </span>
              ))}
          </div>

          <div className="mt-3 text-xs text-gray-400 flex items-center gap-2">
            <Info size={14} /> Server-provided metrics will override client estimates where available.
          </div>
        </div>
      )}
    </div>
  );
}

// Main Column Component
export default function SourceInputColumn({
  // Dropzone props
  getRootProps,
  getInputProps,
  isDragActive,
  // Audio file props
  audioFile,
  audioUrl,
  isPlaying,
  toggleAudioPlayback,
  // Recording props
  isRecording,
  isTranscribing,
  uploadingRecording,
  uploadProgress,
  startRecording,
  stopRecording,
  // Source text props
  sourceText,
  onSourceTextChange,
  translateText,
  isTranslating,
  downloadTXT,
  // Glossary props
  glossaryOpen,
  setGlossaryOpen,
  glossaryRules,
  newRule,
  setNewRule,
  addRule,
  removeRule,
  applyGlossary,
  detectedLanguage,
  selectedLanguage,
  // State props
  segmentState,
  translatedText,
}) {
  return (
    <GlassCard className="space-y-6">
      {/* Upload */}
      <div>
        <SectionTitle>Upload Audio File</SectionTitle>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
            isDragActive ? 'border-indigo-500 bg-indigo-500/10' : 'border-gray-700 hover:border-gray-500'
          } ${isTranscribing || isRecording || segmentState === 'finalized' ? 'pointer-events-none opacity-50' : ''}`}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto mb-2 text-gray-400" size={32} />
          <p className="text-gray-400">
            {isRecording ? 'Stop recording to upload' : (isDragActive ? 'Drop the audio file here' : 'Drag & drop an audio file here, or click to select')}
          </p>
          <p className="text-sm text-gray-500 mt-1">MP3, WAV, FLAC, M4A, MP4, MOV, AVI, WebM, OGG, etc.</p>
        </div>

        {audioFile && (
          <div className="mt-3 p-3 bg-gray-800/60 rounded-lg border border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileAudio size={20} className="text-blue-400" />
                <span className="text-sm text-gray-300 truncate">{audioFile.name}</span>
              </div>
              {audioUrl && (
                <button onClick={toggleAudioPlayback} className="p-1 text-gray-300 hover:text-white transition-colors">
                  {isPlaying ? <Pause size={16} /> : <Play size={16} />}
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Recording */}
      <div className="text-center">
        <SectionTitle>Live Recording</SectionTitle>
        <PrimaryButton
          onClick={isRecording ? stopRecording : startRecording}
          disabled={uploadingRecording || isTranscribing || segmentState === 'finalized'}
          className="w-48"
        >
          {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
          {isRecording ? 'Stop Recording' : 'Start Recording'}
        </PrimaryButton>

        {(isTranscribing || uploadingRecording) && (
          <div className="mt-4 p-3 bg-gray-800/60 rounded-lg border border-gray-700">
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>{uploadingRecording ? 'Uploading recording...' : 'Processing audio...'}</span>
              <span>{uploadProgress < 100 ? `${uploadProgress}%` : 'Transcribing...'}</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-indigo-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress < 100 ? uploadProgress : 95}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Source Text */}
      <div>
        <SectionTitle>Source Text</SectionTitle>
        <textarea
          value={sourceText}
          onChange={(e) => onSourceTextChange(e.target.value)}
          className="w-full h-40 p-3 bg-gray-800 border border-gray-700 rounded-lg text-white resize-none"
          placeholder="Enter text to translate or upload/record above..."
          disabled={isTranscribing || segmentState === 'finalized'}
        />
        <div className="flex gap-2 mt-3">
          <PrimaryButton
            onClick={() => translateText()}
            disabled={isTranslating || isTranscribing || !sourceText.trim() || segmentState === 'finalized'}
          >
            {isTranslating ? 'Translating...' : 'Translate'}
          </PrimaryButton>
          <button
            onClick={downloadTXT}
            disabled={!translatedText}
            className="px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-gray-300 hover:bg-gray-700 flex items-center gap-2"
          >
            <Download size={16} /> Download TXT
          </button>
        </div>
      </div>

      {/* Glossary drawer */}
      <GlossaryDrawer
        isOpen={glossaryOpen}
        onToggle={() => setGlossaryOpen((s) => !s)}
        rules={glossaryRules}
        newRule={newRule}
        onRuleChange={setNewRule}
        onAddRule={addRule}
        onRemoveRule={removeRule}
        onApplyGlossary={applyGlossary}
        detectedLanguage={detectedLanguage}
        selectedLanguage={selectedLanguage}
        segmentState={segmentState}
        translatedText={translatedText}
      />
    </GlassCard>
  );
}