import React, { useEffect, useState } from 'react';
import '../styles/GPUStatus.css';

interface GPUInfo {
  has_gpu: boolean;
  gpu_name: string | null;
  total_vram: number | null;
  free_vram: number | null;
  used_vram: number | null;
  gpu_type: string | null;
  metal_support: boolean;
}

interface ModelInfo {
  model: string;
  vram_required: number;
  suitable: boolean;
  reason: string;
}

interface GPUStatus {
  gpu_info: GPUInfo;
  current_model: string;
  recommended_model: string;
  vram_required: number;
  suitable_models: ModelInfo[];
  using_gpu: boolean;
}

const GPUStatus: React.FC = () => {
  const [gpuStatus, setGpuStatus] = useState<GPUStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchGPUStatus = async () => {
      try {
        const response = await fetch('/api/gpu-status');
        if (!response.ok) {
          throw new Error('Failed to fetch GPU status');
        }
        const data = await response.json();
        setGpuStatus(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchGPUStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchGPUStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleModelChange = async (modelName: string) => {
    try {
      const response = await fetch('/api/update-model', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model: modelName }),
      });
      
      if (!response.ok) {
        throw new Error('Failed to update model');
      }
      
      // Refresh GPU status
      const statusResponse = await fetch('/api/gpu-status');
      if (statusResponse.ok) {
        const data = await statusResponse.json();
        setGpuStatus(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update model');
    }
  };

  if (loading) {
    return <div className="gpu-status loading">Loading GPU status...</div>;
  }

  if (error) {
    return <div className="gpu-status error">Error: {error}</div>;
  }

  if (!gpuStatus) {
    return <div className="gpu-status error">No GPU status available</div>;
  }

  const formatVRAM = (vram: number | null): string => {
    return vram ? `${vram.toFixed(1)}GB` : 'N/A';
  };

  return (
    <div className="gpu-status">
      <div className="gpu-info">
        <h3>GPU Status</h3>
        {gpuStatus.gpu_info.has_gpu ? (
          <>
            <p className="gpu-name">
              {gpuStatus.gpu_info.gpu_name}
              {gpuStatus.gpu_info.gpu_type && (
                <span className="gpu-type"> ({gpuStatus.gpu_info.gpu_type})</span>
              )}
            </p>
            <div className="vram-info">
              <div>Total VRAM: {formatVRAM(gpuStatus.gpu_info.total_vram)}</div>
              <div>Free VRAM: {formatVRAM(gpuStatus.gpu_info.free_vram)}</div>
              <div>Used VRAM: {formatVRAM(gpuStatus.gpu_info.used_vram)}</div>
            </div>
            <div className="gpu-status-indicator enabled">
              GPU Acceleration: {gpuStatus.using_gpu ? 'Enabled' : 'Disabled'}
              {gpuStatus.gpu_info.metal_support && (
                <div className="metal-support">Metal Support: Available</div>
              )}
            </div>
          </>
        ) : (
          <p className="no-gpu">No compatible GPU detected. Using CPU for inference.</p>
        )}
      </div>

      <div className="model-info">
        <h3>Model Information</h3>
        <div className="current-model">
          <p>Current Model: {gpuStatus.current_model}</p>
          <p>Recommended Model: {gpuStatus.recommended_model} ({gpuStatus.vram_required}GB VRAM)</p>
        </div>

        <div className="model-list">
          <h4>Available Models:</h4>
          <div className="model-grid">
            {gpuStatus.suitable_models.map((model) => (
              <div
                key={model.model}
                className={`model-card ${model.suitable ? 'suitable' : 'unsuitable'}`}
                onClick={() => model.suitable && handleModelChange(model.model)}
              >
                <div className="model-name">{model.model}</div>
                <div className="model-vram">{model.vram_required}GB VRAM</div>
                <div className="model-status">{model.reason}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GPUStatus;