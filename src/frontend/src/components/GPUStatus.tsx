import React, { useEffect, useState } from 'react';

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
    return (
      <div className="text-terminal-amber animate-pulse">
        Loading GPU status...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-500">
        Error: {error}
      </div>
    );
  }

  if (!gpuStatus) {
    return (
      <div className="text-red-500">
        No GPU status available
      </div>
    );
  }

  const formatVRAM = (vram: number | null): string => {
    return vram ? `${vram.toFixed(1)}GB` : 'N/A';
  };

  return (
    <div className="text-terminal-green">
      <div className="mb-6">
        <h3 className="text-terminal-amber text-lg font-bold mb-3">GPU Status</h3>
        {gpuStatus.gpu_info.has_gpu ? (
          <>
            <p className="mb-2">
              <span className="text-terminal-green font-bold">
                {gpuStatus.gpu_info.gpu_name}
              </span>
              {gpuStatus.gpu_info.gpu_type && (
                <span className="text-terminal-green opacity-70 ml-2">
                  ({gpuStatus.gpu_info.gpu_type})
                </span>
              )}
            </p>
            <div className="grid grid-cols-3 gap-4 mb-4 bg-terminal-gray-dark p-3 rounded border border-terminal-green">
              <div>Total VRAM: {formatVRAM(gpuStatus.gpu_info.total_vram)}</div>
              <div>Free VRAM: {formatVRAM(gpuStatus.gpu_info.free_vram)}</div>
              <div>Used VRAM: {formatVRAM(gpuStatus.gpu_info.used_vram)}</div>
            </div>
            <div className="flex items-center gap-2 mb-2">
              <div className={`h-2 w-2 rounded-full ${gpuStatus.using_gpu ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span>GPU Acceleration: {gpuStatus.using_gpu ? 'Enabled' : 'Disabled'}</span>
              {gpuStatus.gpu_info.metal_support && (
                <span className="ml-4 text-terminal-amber">
                  Metal Support: Available
                </span>
              )}
            </div>
          </>
        ) : (
          <p className="text-red-500">
            No compatible GPU detected. Using CPU for inference.
          </p>
        )}
      </div>

      <div>
        <h3 className="text-terminal-amber text-lg font-bold mb-3">Model Information</h3>
        <div className="mb-4 bg-terminal-gray-dark p-3 rounded border border-terminal-green">
          <p>Current Model: {gpuStatus.current_model}</p>
          <p>
            Recommended Model: {gpuStatus.recommended_model} ({gpuStatus.vram_required}GB VRAM)
          </p>
        </div>

        <div>
          <h4 className="text-terminal-amber mb-2">Available Models:</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {gpuStatus.suitable_models.map((model) => (
              <div
                key={model.model}
                onClick={() => model.suitable && handleModelChange(model.model)}
                className={`
                  p-4 rounded border cursor-pointer transition-colors duration-200
                  ${model.suitable 
                    ? 'border-terminal-green hover:bg-terminal-green hover:bg-opacity-10' 
                    : 'border-red-500 opacity-50 cursor-not-allowed'}
                `}
              >
                <div className="font-bold mb-1">{model.model}</div>
                <div className="text-sm opacity-70">{model.vram_required}GB VRAM</div>
                <div className={`text-sm mt-1 ${model.suitable ? 'text-terminal-green' : 'text-red-500'}`}>
                  {model.reason}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default GPUStatus;