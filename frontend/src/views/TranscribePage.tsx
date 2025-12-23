import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useJobStatus, useCancelJob, useDownload, useDownloadVideo, useBurnIn, useStyles } from '../hooks/useTranscription';
import { cn } from '../lib/utils';
import { Check, X, Download, Loader2, Film, Video } from 'lucide-react';

function TranscribePage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();

  const { data: job, isLoading, error } = useJobStatus(jobId || '', !!jobId);
  const cancelJob = useCancelJob();
  const download = useDownload();
  const downloadVideo = useDownloadVideo();
  const burnIn = useBurnIn();
  const { data: styles = [] } = useStyles();

  // Burn-in options state
  const [selectedStyle, setSelectedStyle] = useState<string>('professional');
  const [outputFormat, setOutputFormat] = useState<'mp4' | 'mkv' | 'webm'>('mp4');
  const [quality, setQuality] = useState<'low' | 'medium' | 'high'>('high');

  const handleDownload = () => {
    if (jobId) {
      download.mutate(jobId);
    }
  };

  const handleDownloadVideo = () => {
    if (jobId && job) {
      downloadVideo.mutate({ jobId, filename: job.filename });
    }
  };

  const handleCancel = () => {
    if (jobId) {
      cancelJob.mutate(jobId);
    }
  };

  const handleBurnIn = () => {
    if (jobId) {
      burnIn.mutate({
        jobId,
        request: {
          style_id: selectedStyle,
          output_format: outputFormat,
          quality,
        },
      });
    }
  };

  const statusConfig = {
    pending: { label: 'Pending', color: 'text-neutral-400', bg: 'bg-neutral-400/20' },
    uploading: { label: 'Uploading', color: 'text-blue-400', bg: 'bg-blue-400/20' },
    queued: { label: 'Queued', color: 'text-yellow-400', bg: 'bg-yellow-400/20' },
    processing: { label: 'Processing', color: 'text-primary', bg: 'bg-primary/20' },
    post_processing: { label: 'Post-Processing', color: 'text-purple-400', bg: 'bg-purple-400/20' },
    completed: { label: 'Completed', color: 'text-success', bg: 'bg-success/20' },
    failed: { label: 'Failed', color: 'text-error', bg: 'bg-error/20' },
    cancelled: { label: 'Cancelled', color: 'text-neutral-400', bg: 'bg-neutral-400/20' },
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="max-w-md mx-auto text-center">
        <div className="w-16 h-16 rounded-full bg-error/20 flex items-center justify-center mx-auto mb-4">
          <X className="w-8 h-8 text-error" />
        </div>
        <h2 className="text-xl font-semibold mb-2">Job Not Found</h2>
        <p className="text-neutral-400 mb-6">
          The transcription job could not be found.
        </p>
        <button
          onClick={() => navigate('/')}
          className="px-6 py-2 bg-primary hover:bg-primary/90 rounded-lg font-medium"
        >
          Go Back
        </button>
      </div>
    );
  }

  const config = statusConfig[job.status as keyof typeof statusConfig] || statusConfig.pending;

  return (
    <div className="max-w-2xl mx-auto">
      <button
        onClick={() => navigate('/')}
        className="text-neutral-400 hover:text-neutral-200 text-sm mb-6"
      >
        Back to Home
      </button>

      <div className="glass rounded-xl p-6 space-y-6">
        {/* Status Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-1">{job.filename}</h1>
            <p className="text-sm text-neutral-400">
              ID: {job.job_id}
            </p>
          </div>
          <span className={cn('px-3 py-1 rounded-full text-sm font-medium', config.color, config.bg)}>
            {config.label}
          </span>
        </div>

        {/* Progress Bar */}
        {job.status === 'processing' || job.status === 'uploading' || job.status === 'post_processing' ? (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-neutral-400">Progress</span>
              <span className="font-medium">{job.progress.toFixed(1)}%</span>
            </div>
            <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-300 ease-out"
                style={{ width: `${job.progress}%` }}
              />
            </div>
          </div>
        ) : null}

        {/* Details */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-neutral-400">Detected Language</span>
            <p className="font-medium">{job.detected_language || 'N/A'}</p>
          </div>
          <div>
            <span className="text-neutral-400">Processing Time</span>
            <p className="font-medium">
              {job.processing_time_seconds ? `${job.processing_time_seconds.toFixed(2)}s` : 'N/A'}
            </p>
          </div>
          {job.vram_used_mb !== null && (
            <div>
              <span className="text-neutral-400">VRAM Used</span>
              <p className="font-medium">{job.vram_used_mb} MB</p>
            </div>
          )}
          <div>
            <span className="text-neutral-400">Created</span>
            <p className="font-medium">{new Date(job.created_at).toLocaleString()}</p>
          </div>
        </div>

        {/* Error Message */}
        {job.status === 'failed' && job.error_message && (
          <div className="p-4 bg-error/20 border border-error/30 rounded-lg">
            <p className="text-sm text-error">{job.error_message}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          {job.status === 'completed' && (
            <>
              {job.video_output_path ? (
                // Video download button when auto burn-in was enabled
                <button
                  onClick={handleDownloadVideo}
                  disabled={downloadVideo.isPending}
                  className={cn(
                    'flex-1 py-2.5 px-4 rounded-lg font-medium transition-colors',
                    'bg-success hover:bg-success/90',
                    'flex items-center justify-center gap-2',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  {downloadVideo.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Downloading...
                    </>
                  ) : (
                    <>
                      <Video className="w-4 h-4" />
                      Download Video with Subtitles
                    </>
                  )}
                </button>
              ) : (
                // Subtitle download button when auto burn-in was not enabled
                <button
                  onClick={handleDownload}
                  disabled={download.isPending}
                  className={cn(
                    'flex-1 py-2.5 px-4 rounded-lg font-medium transition-colors',
                    'bg-primary hover:bg-primary/90',
                    'flex items-center justify-center gap-2',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  {download.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Downloading...
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4" />
                      Download Subtitles
                    </>
                  )}
                </button>
              )}
            </>
          )}

          {(job.status === 'processing' || job.status === 'queued' || job.status === 'uploading') && (
            <button
              onClick={handleCancel}
              disabled={cancelJob.isPending}
              className={cn(
                'px-6 py-2.5 rounded-lg font-medium transition-colors',
                'bg-error hover:bg-error/90',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {cancelJob.isPending ? 'Cancelling...' : 'Cancel'}
            </button>
          )}

          {(job.status === 'failed' || job.status === 'cancelled') && (
            <button
              onClick={() => navigate('/')}
              className="flex-1 py-2.5 px-4 rounded-lg font-medium bg-neutral-700 hover:bg-neutral-600 transition-colors"
            >
              Start New Transcription
            </button>
          )}
        </div>

        {/* Burn-in Section - only show if video wasn't auto-generated */}
        {job.status === 'completed' && !job.video_output_path && (
          <div className="pt-6 border-t border-neutral-700/50">
            <div className="flex items-center gap-2 mb-4">
              <Film className="w-5 h-5 text-primary" />
              <h3 className="text-lg font-semibold">Burn Subtitles to Video</h3>
            </div>
            <p className="text-sm text-neutral-400 mb-4">
              Create a new video file with subtitles permanently embedded (hard-subs).
            </p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              {/* Style Selector */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-neutral-300">Subtitle Style</label>
                <select
                  value={selectedStyle}
                  onChange={(e) => setSelectedStyle(e.target.value)}
                  className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  {styles.map((style: any) => (
                    <option key={style.id} value={style.id}>
                      {style.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Format Selector */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-neutral-300">Output Format</label>
                <select
                  value={outputFormat}
                  onChange={(e) => setOutputFormat(e.target.value as 'mp4' | 'mkv' | 'webm')}
                  className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="mp4">MP4 (H.264)</option>
                  <option value="mkv">MKV</option>
                  <option value="webm">WebM</option>
                </select>
              </div>

              {/* Quality Selector */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-neutral-300">Quality</label>
                <select
                  value={quality}
                  onChange={(e) => setQuality(e.target.value as 'low' | 'medium' | 'high')}
                  className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="low">Low (faster)</option>
                  <option value="medium">Medium</option>
                  <option value="high">High (H.265)</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleBurnIn}
              disabled={burnIn.isPending}
              className={cn(
                'w-full py-2.5 px-4 rounded-lg font-medium transition-colors',
                'bg-secondary hover:bg-secondary/90',
                'flex items-center justify-center gap-2',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {burnIn.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Processing Video...
                </>
              ) : (
                <>
                  <Video className="w-4 h-4" />
                  Burn & Download Video
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default TranscribePage;
