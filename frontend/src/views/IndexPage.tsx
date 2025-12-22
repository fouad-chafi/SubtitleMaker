import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUpload } from '../hooks/useTranscription';
import { useLanguages } from '../hooks/useTranscription';
import { cn } from '../lib/utils';
import { Upload, FileVideo, Settings as SettingsIcon, Check } from 'lucide-react';
import type { SubtitleFormat } from '../types';

const subtitleFormats: { value: SubtitleFormat; label: string }[] = [
  { value: 'srt', label: 'SRT (SubRip)' },
  { value: 'vtt', label: 'WebVTT' },
  { value: 'ass', label: 'ASS (Advanced SubStation)' },
  { value: 'txt', label: 'Plain Text' },
  { value: 'json', label: 'JSON' },
];

function IndexPage() {
  const navigate = useNavigate();
  const upload = useUpload();
  const { data: languages } = useLanguages();

  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [options, setOptions] = useState({
    language: '',
    task: 'transcribe' as 'transcribe' | 'translate',
    vad_filter: true,
    word_timestamps: true,
    subtitle_format: 'srt' as SubtitleFormat,
    num_speakers: null as number | null,
  });

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('video/') || file.type.startsWith('audio/')) {
        setSelectedFile(file);
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    try {
      const result = await upload.mutateAsync({
        file: selectedFile,
        options,
      });
      navigate(`/transcribe/${result.job_id}`);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
          AI-Powered Subtitles
        </h1>
        <p className="text-neutral-400 text-lg">
          Generate accurate subtitles for your videos using Whisper AI
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Upload Zone */}
        <div
          onDrop={handleDrop}
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          className={cn(
            'border-2 border-dashed rounded-xl p-12 text-center transition-all',
            'hover:border-primary/50 hover:bg-white/5',
            isDragging ? 'border-primary bg-primary/5' : 'border-neutral-700',
            selectedFile && 'border-success bg-success/5'
          )}
        >
          <input
            type="file"
            accept="video/*,audio/*"
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
          />
          <label htmlFor="file-upload" className="cursor-pointer">
            <div className="flex flex-col items-center gap-4">
              {selectedFile ? (
                <>
                  <div className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center">
                    <Check className="w-8 h-8 text-success" />
                  </div>
                  <div>
                    <p className="text-lg font-medium">{selectedFile.name}</p>
                    <p className="text-sm text-neutral-400">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      setSelectedFile(null);
                    }}
                    className="text-sm text-neutral-400 hover:text-neutral-200"
                  >
                    Choose different file
                  </button>
                </>
              ) : (
                <>
                  <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
                    <Upload className="w-8 h-8 text-primary" />
                  </div>
                  <div>
                    <p className="text-lg font-medium">
                      Drop your video or audio file here
                    </p>
                    <p className="text-sm text-neutral-400 mt-1">
                      or click to browse
                    </p>
                  </div>
                  <p className="text-xs text-neutral-500">
                    Supports MP4, MOV, AVI, MKV, WEBM, MP3, WAV, M4A
                  </p>
                </>
              )}
            </div>
          </label>
        </div>

        {/* Options */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Language */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-neutral-300">Language</label>
            <select
              value={options.language}
              onChange={(e) => setOptions({ ...options, language: e.target.value })}
              className="w-full bg-neutral-900 border border-neutral-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Auto-detect</option>
              {languages &&
                Object.entries(languages).map(([code, name]) => (
                  <option key={code} value={code}>
                    {name}
                  </option>
                ))}
            </select>
          </div>

          {/* Format */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-neutral-300">Output Format</label>
            <select
              value={options.subtitle_format}
              onChange={(e) =>
                setOptions({ ...options, subtitle_format: e.target.value as SubtitleFormat })
              }
              className="w-full bg-neutral-900 border border-neutral-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {subtitleFormats.map((format) => (
                <option key={format.value} value={format.value}>
                  {format.label}
                </option>
              ))}
            </select>
          </div>

          {/* Task */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-neutral-300">Task</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="task"
                  value="transcribe"
                  checked={options.task === 'transcribe'}
                  onChange={() => setOptions({ ...options, task: 'transcribe' })}
                  className="w-4 h-4 text-primary focus:ring-primary"
                />
                <span className="text-sm">Transcribe</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="task"
                  value="translate"
                  checked={options.task === 'translate'}
                  onChange={() => setOptions({ ...options, task: 'translate' })}
                  className="w-4 h-4 text-primary focus:ring-primary"
                />
                <span className="text-sm">Translate to English</span>
              </label>
            </div>
          </div>

          {/* Speakers */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-neutral-300">
              Number of Speakers
            </label>
            <select
              value={options.num_speakers || ''}
              onChange={(e) =>
                setOptions({
                  ...options,
                  num_speakers: e.target.value ? parseInt(e.target.value) : null,
                })
              }
              className="w-full bg-neutral-900 border border-neutral-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Auto-detect</option>
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                <option key={n} value={n}>
                  {n} speaker{n > 1 ? 's' : ''}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Toggles */}
        <div className="flex flex-wrap gap-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={options.vad_filter}
              onChange={(e) => setOptions({ ...options, vad_filter: e.target.checked })}
              className="w-4 h-4 text-primary focus:ring-primary rounded"
            />
            <span className="text-sm text-neutral-300">VAD Filter</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={options.word_timestamps}
              onChange={(e) => setOptions({ ...options, word_timestamps: e.target.checked })}
              className="w-4 h-4 text-primary focus:ring-primary rounded"
            />
            <span className="text-sm text-neutral-300">Word Timestamps</span>
          </label>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={!selectedFile || upload.isPending}
          className={cn(
            'w-full py-3 px-6 rounded-lg font-medium transition-colors',
            'bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed',
            'flex items-center justify-center gap-2'
          )}
        >
          {upload.isPending ? (
            <>
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <FileVideo className="w-5 h-5" />
              Generate Subtitles
            </>
          )}
        </button>
      </form>
    </div>
  );
}

export default IndexPage;
