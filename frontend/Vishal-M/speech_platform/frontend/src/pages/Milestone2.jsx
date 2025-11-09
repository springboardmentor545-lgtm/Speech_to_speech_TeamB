// src/pages/Milestone2.jsx
import React from 'react';

// Centralized utilities & data
import { LANGUAGES, SOURCE_LANGUAGES } from '../utils/constants';
import { useMilestone2Logic } from '../hooks/useMilestone2Logic';

// UI components
import Tag from '../components/ui/Tag';
import SourceInputColumn from '../components/milestone2/SourceInputColumn';
import TranslationOutputColumn from '../components/milestone2/TranslationOutputColumn';
// Removed: LiveStreamCard import

const Milestone2 = () => {
  // ✅ All logic, state, and effects are now in this single custom hook.
  const logic = useMilestone2Logic();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <h1 className="text-3xl font-bold">Milestone 2: Translation Model Development</h1>
        <Tag color="blue">Pro</Tag>
      </div>
      <p className="text-gray-400">Upload/record audio → transcribe → translate. Glossary + metrics + analytics.</p>

      {logic.error && (
        <div className="p-4 bg-red-500/20 text-red-300 rounded-lg border border-red-500">
          <strong>Error:</strong> {logic.error}
        </div>
      )}

      {/* Removed: Live stream error box */}

      {/* Source language */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Source Language (for upload/recording)</label>
        <select
          value={logic.sourceLanguage}
          onChange={(e) => logic.setSourceLanguage(e.target.value)}
          className="w-full p-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
          disabled={logic.isBusy || logic.isTranscribing || logic.segmentState === 'finalized'}
        >
          {SOURCE_LANGUAGES.map((lang) => (
            <option key={lang.code} value={lang.code}>{lang.name}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SourceInputColumn
          // Dropzone
          getRootProps={logic.getRootProps}
          getInputProps={logic.getInputProps}
          isDragActive={logic.isDragActive}
          // Audio
          audioFile={logic.audioFile}
          audioUrl={logic.audioUrl}
          isPlaying={logic.isPlaying}
          toggleAudioPlayback={logic.toggleAudioPlayback}
          // Recording
          isRecording={logic.isRecording}
          isTranscribing={logic.isTranscribing}
          uploadingRecording={logic.uploadingRecording}
          uploadProgress={logic.uploadProgress}
          startRecording={logic.startRecording}
          stopRecording={logic.stopRecording}
          // Source Text
          sourceText={logic.sourceText}
          onSourceTextChange={logic.setSourceText}
          translateText={logic.translateText}
          isTranslating={logic.isTranslating}
          downloadTXT={logic.downloadTXT}
          // Glossary
          glossaryOpen={logic.glossaryOpen}
          setGlossaryOpen={logic.setGlossaryOpen}
          glossaryRules={logic.glossaryRules}
          newRule={logic.newRule}
          setNewRule={logic.setNewRule}
          addRule={logic.addRule}
          removeRule={logic.removeRule}
          applyGlossary={logic.applyGlossary}
          // State
          detectedLanguage={logic.detectedLanguage}
          selectedLanguage={logic.selectedLanguage}
          segmentState={logic.segmentState}
          translatedText={logic.translatedText}
          isBusy={logic.isBusy} // Pass busy state
        />

        <TranslationOutputColumn
          // Language
          languages={LANGUAGES}
          selectedLanguage={logic.selectedLanguage}
          onLanguageChange={logic.setSelectedLanguage}
          // Translation
          isTranslating={logic.isTranslating}
          translatedText={logic.translatedText}
          // Segment
          segmentState={logic.segmentState}
          onSegmentStateChange={logic.setSegmentState}
          applyGlossary={logic.applyGlossary}
          downloadTXT={logic.downloadTXT}
          // Metrics
          metrics={logic.metrics}
          metricsHistory={logic.metricsHistory}
          languageConfidence={logic.languageConfidence}
          // Details
          detectedLanguage={logic.detectedLanguage}
          transcriptId={logic.transcriptId}
        />
      </div>

      {/* Removed: LiveStreamCard component */}

    </div>
  );
};

export default Milestone2;