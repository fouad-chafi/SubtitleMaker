export type JobStatus = 'pending' | 'uploading' | 'queued' | 'processing' | 'post_processing' | 'completed' | 'failed' | 'cancelled';

export type SubtitleFormat = 'srt' | 'vtt' | 'ass' | 'txt' | 'json';

export interface TranscriptionRequest {
  language?: string | null;
  task?: 'transcribe' | 'translate';
  vad_filter?: boolean;
  word_timestamps?: boolean;
  subtitle_format?: SubtitleFormat;
  num_speakers?: number | null;
}

export interface TranscriptionJob {
  job_id: string;
  status: JobStatus;
  progress: number;
  filename: string;
  detected_language?: string | null;
  output_path?: string | null;
  error_message?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  processing_time_seconds?: number | null;
  vram_used_mb?: number | null;
}

export interface UploadResponse {
  job_id: string;
  filename: string;
  file_size_mb: number;
  status: string;
  created_at: string;
}

export interface SubtitleStyle {
  id: string;
  name: string;
  font_family: string;
  font_size: number;
  font_color: string;
  background_color: string;
  background_opacity: number;
  outline_color: string;
  outline_width: number;
  position: 'top' | 'center' | 'bottom';
  alignment: 'left' | 'center' | 'right';
}

export interface GPUInfo {
  available: boolean;
  device_name?: string;
  vram_total_mb: number;
  vram_used_mb: number;
  vram_free_mb: number;
  temperature_c?: number | null;
}
