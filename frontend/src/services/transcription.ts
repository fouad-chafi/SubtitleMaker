import apiClient from '../lib/api';
import type { TranscriptionJob, TranscriptionRequest, UploadResponse } from '../types';

export async function uploadFile(
  file: File,
  options: TranscriptionRequest = {}
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  if (options.language) formData.append('language', options.language);
  if (options.task) formData.append('task', options.task);
  if (options.vad_filter !== undefined) formData.append('vad_filter', String(options.vad_filter));
  if (options.word_timestamps !== undefined) formData.append('word_timestamps', String(options.word_timestamps));
  if (options.subtitle_format) formData.append('subtitle_format', options.subtitle_format);
  if (options.num_speakers) formData.append('num_speakers', String(options.num_speakers));

  const response = await apiClient.post<UploadResponse>('/transcribe', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
}

export async function getJobStatus(jobId: string): Promise<TranscriptionJob> {
  const response = await apiClient.get<TranscriptionJob>(`/transcribe/${jobId}`);
  return response.data;
}

export async function listJobs(
  status?: string,
  limit = 50,
  offset = 0
): Promise<{ jobs: TranscriptionJob[]; total: number }> {
  const params: Record<string, string | number> = { limit, offset };
  if (status) params.status = status;

  const response = await apiClient.get('/jobs', { params });
  return {
    jobs: response.data.jobs,
    total: response.data.total,
  };
}

export async function cancelJob(jobId: string): Promise<void> {
  await apiClient.post(`/jobs/${jobId}/cancel`);
}

export async function deleteJob(jobId: string): Promise<void> {
  await apiClient.delete(`/jobs/${jobId}`);
}

export async function downloadSubtitle(jobId: string): Promise<void> {
  const response = await apiClient.get(`/transcribe/${jobId}/download`, {
    responseType: 'blob',
  });

  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;

  const filename = response.headers['content-disposition']?.match(/filename="?(.+)"?/)?.[1] || `subtitle.${jobId}`;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export async function getStyles(): Promise<any[]> {
  const response = await apiClient.get('/styles');
  return response.data.styles;
}

export async function getLanguages(): Promise<Record<string, string>> {
  const response = await apiClient.get('/languages');
  return response.data.languages;
}

export async function getHealthStatus(): Promise<{
  status: string;
  version: string;
  gpu_available: boolean;
  gpu_device_name?: string;
}> {
  const response = await apiClient.get('/health');
  return response.data;
}

export async function getGPUInfo(): Promise<{
  available: boolean;
  device_name?: string;
  vram_total_mb: number;
  vram_used_mb: number;
  vram_free_mb: number;
}> {
  const response = await apiClient.get('/health/gpu');
  return response.data;
}
