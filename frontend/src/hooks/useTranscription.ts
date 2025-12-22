import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  uploadFile,
  getJobStatus,
  listJobs,
  cancelJob,
  deleteJob,
  downloadSubtitle,
  getStyles,
  getLanguages,
  getHealthStatus,
  getGPUInfo,
} from '../services/transcription';
import type { TranscriptionRequest } from '../types';

export function useUpload() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, options }: { file: File; options: TranscriptionRequest }) =>
      uploadFile(file, options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

export function useJobStatus(jobId: string, enabled = true) {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => getJobStatus(jobId),
    enabled: enabled && !!jobId,
    refetchInterval: (query) => {
      const job = query.state.data;
      // Poll more frequently during processing
      if (job?.status === 'processing' || job?.status === 'uploading') {
        return 2000;
      }
      return false;
    },
  });
}

export function useJobs(status?: string, limit = 50) {
  return useQuery({
    queryKey: ['jobs', status, limit],
    queryFn: () => listJobs(status, limit),
  });
}

export function useCancelJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: string) => cancelJob(jobId),
    onSuccess: (_, jobId) => {
      queryClient.invalidateQueries({ queryKey: ['job', jobId] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

export function useDeleteJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: string) => deleteJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

export function useDownload() {
  return useMutation({
    mutationFn: (jobId: string) => downloadSubtitle(jobId),
  });
}

export function useStyles() {
  return useQuery({
    queryKey: ['styles'],
    queryFn: getStyles,
  });
}

export function useLanguages() {
  return useQuery({
    queryKey: ['languages'],
    queryFn: getLanguages,
  });
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: getHealthStatus,
    retry: false,
  });
}

export function useGPUInfo() {
  return useQuery({
    queryKey: ['gpu'],
    queryFn: getGPUInfo,
    refetchInterval: 5000,
    retry: false,
  });
}
