import { useHealth, useGPUInfo } from '../hooks/useTranscription';
import { cn } from '../lib/utils';
import { Cpu, HardDrive, Thermometer, Check, X } from 'lucide-react';

function SettingsPage() {
  const { data: health } = useHealth();
  const { data: gpu } = useGPUInfo();

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-neutral-400 mt-1">Configure your transcription experience</p>
      </div>

      {/* System Status */}
      <section className="space-y-4">
        <h2 className="text-lg font-semibold">System Status</h2>

        <div className="glass rounded-xl p-6 space-y-6">
          {/* API Status */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-success/20">
                <Check className="w-5 h-5 text-success" />
              </div>
              <div>
                <p className="font-medium">API Connection</p>
                <p className="text-sm text-neutral-400">
                  Version {health?.version || 'N/A'}
                </p>
              </div>
            </div>
            <span className="px-3 py-1 rounded-full text-sm font-medium text-success bg-success/20">
              Healthy
            </span>
          </div>

          {/* GPU Status */}
          <div className="border-t border-white/10 pt-6">
            <div className="flex items-center gap-2 mb-4">
              <Cpu className="w-5 h-5 text-primary" />
              <h3 className="font-medium">GPU Information</h3>
            </div>

            {gpu?.available ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-neutral-400">Device</p>
                    <p className="font-medium">{gpu.device_name || 'Unknown'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-neutral-400">Total VRAM</p>
                    <p className="font-medium">{gpu.vram_total_mb} MB</p>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-neutral-400">Memory Usage</span>
                    <span className="font-medium">
                      {gpu.vram_used_mb} / {gpu.vram_total_mb} MB
                    </span>
                  </div>
                  <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all"
                      style={{
                        width: `${(gpu.vram_used_mb / gpu.vram_total_mb) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-3 text-neutral-400">
                <X className="w-5 h-5" />
                <p>GPU not available. Running on CPU.</p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Note about settings */}
      <section className="glass rounded-xl p-6">
        <p className="text-sm text-neutral-400">
          Additional settings will be available in future updates, including:
        </p>
        <ul className="mt-3 space-y-2 text-sm text-neutral-300">
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-primary" />
            Custom subtitle style editor
          </li>
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-primary" />
            Model selection (tiny, base, small, medium, large)
          </li>
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-primary" />
            Batch processing preferences
          </li>
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-primary" />
            Post-processing options
          </li>
        </ul>
      </section>
    </div>
  );
}

export default SettingsPage;
