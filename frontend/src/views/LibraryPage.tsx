import { useJobs, useDeleteJob } from '../hooks/useTranscription';
import { cn } from '../lib/utils';
import { FileVideo, Trash2, Download, Check, X, Loader2, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

function LibraryPage() {
  const navigate = useNavigate();
  const { data, isLoading } = useJobs();
  const deleteJob = useDeleteJob();

  const statusConfig = {
    pending: { icon: Clock, color: 'text-neutral-400', bg: 'bg-neutral-400/20' },
    uploading: { icon: Loader2, color: 'text-blue-400', bg: 'bg-blue-400/20' },
    queued: { icon: Clock, color: 'text-yellow-400', bg: 'bg-yellow-400/20' },
    processing: { icon: Loader2, color: 'text-primary', bg: 'bg-primary/20' },
    post_processing: { icon: Loader2, color: 'text-purple-400', bg: 'bg-purple-400/20' },
    completed: { icon: Check, color: 'text-success', bg: 'bg-success/20' },
    failed: { icon: X, color: 'text-error', bg: 'bg-error/20' },
    cancelled: { icon: X, color: 'text-neutral-400', bg: 'bg-neutral-400/20' },
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const jobs = data?.jobs || [];

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Library</h1>
          <p className="text-neutral-400 mt-1">
            {jobs.length} {jobs.length === 1 ? 'job' : 'jobs'}
          </p>
        </div>
      </div>

      {jobs.length === 0 ? (
        <div className="text-center py-16">
          <FileVideo className="w-16 h-16 text-neutral-700 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">No transcriptions yet</h2>
          <p className="text-neutral-400 mb-6">
            Upload a video to get started
          </p>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-2 bg-primary hover:bg-primary/90 rounded-lg font-medium"
          >
            Upload Video
          </button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => {
            const config = statusConfig[job.status as keyof typeof statusConfig];
            const StatusIcon = config.icon;

            return (
              <div
                key={job.job_id}
                className="glass rounded-xl p-5 space-y-4 hover:bg-white/5 transition-colors cursor-pointer"
                onClick={() => navigate(`/transcribe/${job.job_id}`)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <div className={cn('p-1.5 rounded-lg', config.bg)}>
                      <StatusIcon className={cn('w-4 h-4', config.color, config.icon === Loader2 && 'animate-spin')} />
                    </div>
                    <span className="text-sm font-medium capitalize">{job.status}</span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm('Delete this job?')) {
                        deleteJob.mutate(job.job_id);
                      }
                    }}
                    className="p-1.5 hover:bg-error/20 rounded-lg transition-colors"
                    disabled={deleteJob.isPending}
                  >
                    <Trash2 className="w-4 h-4 text-neutral-400 hover:text-error" />
                  </button>
                </div>

                <div>
                  <h3 className="font-medium truncate" title={job.filename}>
                    {job.filename}
                  </h3>
                  <p className="text-sm text-neutral-400 mt-1">
                    {new Date(job.created_at).toLocaleDateString()}
                  </p>
                </div>

                {job.detected_language && (
                  <div className="text-sm">
                    <span className="text-neutral-400">Language:</span>{' '}
                    <span className="font-medium">{job.detected_language}</span>
                  </div>
                )}

                {job.status === 'processing' && job.progress > 0 && (
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-neutral-400">Progress</span>
                      <span>{job.progress.toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 bg-neutral-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary transition-all"
                        style={{ width: `${job.progress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default LibraryPage;
