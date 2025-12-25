import React, { useState } from 'react';
import { Card } from '../atoms/Card';
import { Button } from '../atoms/Button';
import { Alert } from '../atoms/Alert';
import { Modal } from '../atoms/Modal';
import { useConfigStore, useTrainingStore } from '../../lib/store';

export const ConfigurationPanel: React.FC = () => {
  const { config, updateConfig, savePreset, loadPreset, presets } = useConfigStore();
  const { startTraining } = useTrainingStore();
  
  const [localConfig, setLocalConfig] = useState(config);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [showPresetModal, setShowPresetModal] = useState(false);
  const [presetName, setPresetName] = useState('');

  console.log('[ConfigurationPanel] Rendering:', { config: localConfig, presetsCount: presets.length });

  const validateConfig = () => {
    const errors: string[] = [];
    
    if (localConfig.training.learning_rate <= 0) {
      errors.push('Learning rate must be greater than 0');
    }
    
    if (localConfig.training.batch_size < 1 || localConfig.training.batch_size > 512) {
      errors.push('Batch size must be between 1 and 512');
    }
    
    if (localConfig.training.epochs < 1 || localConfig.training.epochs > 100) {
      errors.push('Epochs must be between 1 and 100');
    }
    
    if (localConfig.nodes.count < 1 || localConfig.nodes.count > 50) {
      errors.push('Node count must be between 1 and 50');
    }
    
    if (localConfig.blockchain.reward_pool <= 0) {
      errors.push('Reward pool must be greater than 0');
    }
    
    console.log('[ConfigurationPanel] Validation result:', { errorsCount: errors.length, errors });
    setValidationErrors(errors);
    return errors.length === 0;
  };

  const handleStartTraining = () => {
    console.log('[ConfigurationPanel] Start training clicked');
    
    if (validateConfig()) {
      updateConfig(localConfig);
      startTraining();
      console.log('[ConfigurationPanel] Training started with config:', localConfig);
    }
  };

  const handleSavePreset = () => {
    console.log('[ConfigurationPanel] Save preset:', presetName);
    
    if (presetName.trim()) {
      savePreset(presetName, localConfig);
      setPresetName('');
      setShowPresetModal(false);
    }
  };

  const handleLoadPreset = (name: string) => {
    console.log('[ConfigurationPanel] Load preset:', name);
    const preset = presets.find(p => p.name === name);
    
    if (preset) {
      setLocalConfig(preset.config);
    }
  };

  const handleExportConfig = () => {
    console.log('[ConfigurationPanel] Export config');
    const dataStr = JSON.stringify(localConfig, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `training-config-${Date.now()}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const handleImportConfig = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    
    if (file) {
      console.log('[ConfigurationPanel] Import config from file:', file.name);
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const imported = JSON.parse(e.target?.result as string);
          setLocalConfig(imported);
          console.log('[ConfigurationPanel] Config imported successfully');
        } catch (error) {
          console.error('[ConfigurationPanel] Import failed:', error);
          setValidationErrors(['Failed to import configuration file']);
        }
      };
      
      reader.readAsText(file);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Configuration</h1>
          <p className="text-gray-600 mt-1">
            Configure training parameters and start sessions
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowPresetModal(true)}
          >
            💾 Save Preset
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportConfig}
          >
            📤 Export
          </Button>
          <label>
            <input
              type="file"
              accept=".json"
              className="hidden"
              onChange={handleImportConfig}
            />
            <Button
              variant="outline"
              size="sm"
            >
              📥 Import
            </Button>
          </label>
        </div>
      </div>

      {/* Validation Errors */}
      {validationErrors.length > 0 && (
        <Alert
          type="error"
          title="Configuration Errors"
          message={validationErrors.join(', ')}
          onClose={() => setValidationErrors([])}
        />
      )}

      {/* Training Configuration */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Training Parameters</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Model Type
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={localConfig.training.model_type}
              onChange={(e) => {
                console.log('[ConfigurationPanel] Model type changed:', e.target.value);
                setLocalConfig({
                  ...localConfig,
                  training: { ...localConfig.training, model_type: e.target.value },
                });
              }}
            >
              <option value="simple_cnn">Simple CNN</option>
              <option value="resnet">ResNet</option>
              <option value="vgg">VGG</option>
              <option value="mobilenet">MobileNet</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Dataset
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={localConfig.training.dataset}
              onChange={(e) => {
                console.log('[ConfigurationPanel] Dataset changed:', e.target.value);
                setLocalConfig({
                  ...localConfig,
                  training: { ...localConfig.training, dataset: e.target.value },
                });
              }}
            >
              <option value="MNIST">MNIST</option>
              <option value="CIFAR-10">CIFAR-10</option>
              <option value="CIFAR-100">CIFAR-100</option>
              <option value="ImageNet">ImageNet</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Learning Rate
            </label>
            <input
              type="number"
              step="0.0001"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={localConfig.training.learning_rate}
              onChange={(e) => {
                console.log('[ConfigurationPanel] Learning rate changed:', e.target.value);
                setLocalConfig({
                  ...localConfig,
                  training: { ...localConfig.training, learning_rate: parseFloat(e.target.value) },
                });
              }}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Batch Size
            </label>
            <input
              type="number"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={localConfig.training.batch_size}
              onChange={(e) => {
                console.log('[ConfigurationPanel] Batch size changed:', e.target.value);
                setLocalConfig({
                  ...localConfig,
                  training: { ...localConfig.training, batch_size: parseInt(e.target.value) },
                });
              }}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Epochs
            </label>
            <input
              type="number"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={localConfig.training.epochs}
              onChange={(e) => {
                console.log('[ConfigurationPanel] Epochs changed:', e.target.value);
                setLocalConfig({
                  ...localConfig,
                  training: { ...localConfig.training, epochs: parseInt(e.target.value) },
                });
              }}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Optimizer
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={localConfig.training.optimizer}
              onChange={(e) => {
                console.log('[ConfigurationPanel] Optimizer changed:', e.target.value);
                setLocalConfig({
                  ...localConfig,
                  training: { ...localConfig.training, optimizer: e.target.value },
                });
              }}
            >
              <option value="adam">Adam</option>
              <option value="sgd">SGD</option>
              <option value="rmsprop">RMSprop</option>
              <option value="adamw">AdamW</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Network Simulation */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Network Simulation</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Network Profile
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={localConfig.network.profile}
              onChange={(e) => {
                console.log('[ConfigurationPanel] Network profile changed:', e.target.value);
                setLocalConfig({
                  ...localConfig,
                  network: { ...localConfig.network, profile: e.target.value },
                });
              }}
            >
              <option value="good">Good (Low Latency)</option>
              <option value="average">Average</option>
              <option value="poor">Poor (High Latency)</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Latency Range (ms)
            </label>
            <div className="flex gap-2">
              <input
                type="number"
                placeholder="Min"
                className="w-1/2 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localConfig.network.latency_range[0]}
                onChange={(e) => {
                  setLocalConfig({
                    ...localConfig,
                    network: {
                      ...localConfig.network,
                      latency_range: [parseInt(e.target.value), localConfig.network.latency_range[1]],
                    },
                  });
                }}
              />
              <input
                type="number"
                placeholder="Max"
                className="w-1/2 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={localConfig.network.latency_range[1]}
                onChange={(e) => {
                  setLocalConfig({
                    ...localConfig,
                    network: {
                      ...localConfig.network,
                      latency_range: [localConfig.network.latency_range[0], parseInt(e.target.value)],
                    },
                  });
                }}
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Packet Loss (%)
            </label>
            <input
              type="number"
              step="0.1"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={localConfig.network.packet_loss}
              onChange={(e) => {
                setLocalConfig({
                  ...localConfig,
                  network: { ...localConfig.network, packet_loss: parseFloat(e.target.value) },
                });
              }}
            />
          </div>
        </div>
      </Card>

      {/* Node Configuration */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Node Configuration</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Number of Nodes
            </label>
            <input
              type="number"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={localConfig.nodes.count}
              onChange={(e) => {
                setLocalConfig({
                  ...localConfig,
                  nodes: { ...localConfig.nodes, count: parseInt(e.target.value) },
                });
              }}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Enable Adaptive Training
            </label>
            <div className="flex items-center h-[42px]">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  checked={localConfig.nodes.adaptive_enabled}
                  onChange={(e) => {
                    setLocalConfig({
                      ...localConfig,
                      nodes: { ...localConfig.nodes, adaptive_enabled: e.target.checked },
                    });
                  }}
                />
                <span className="ml-2 text-sm text-gray-700">Enable</span>
              </label>
            </div>
          </div>
        </div>
      </Card>

      {/* Blockchain Configuration */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Blockchain Configuration</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              RPC Endpoint
            </label>
            <input
              type="text"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={localConfig.blockchain.rpc_endpoint}
              onChange={(e) => {
                setLocalConfig({
                  ...localConfig,
                  blockchain: { ...localConfig.blockchain, rpc_endpoint: e.target.value },
                });
              }}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reward Pool (ETH)
            </label>
            <input
              type="number"
              step="0.01"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={localConfig.blockchain.reward_pool}
              onChange={(e) => {
                setLocalConfig({
                  ...localConfig,
                  blockchain: { ...localConfig.blockchain, reward_pool: parseFloat(e.target.value) },
                });
              }}
            />
          </div>
        </div>
      </Card>

      {/* Presets */}
      {presets.length > 0 && (
        <Card>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Saved Presets</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {presets.map((preset) => (
              <Button
                key={preset.name}
                variant="outline"
                onClick={() => handleLoadPreset(preset.name)}
                className="justify-start"
              >
                📋 {preset.name}
              </Button>
            ))}
          </div>
        </Card>
      )}

      {/* Control Buttons */}
      <div className="flex gap-4">
        <Button
          variant="primary"
          size="lg"
          className="flex-1"
          onClick={handleStartTraining}
        >
          🚀 Start Training
        </Button>
        <Button
          variant="outline"
          size="lg"
          onClick={() => {
            console.log('[ConfigurationPanel] Reset to defaults');
            setLocalConfig(config);
            setValidationErrors([]);
          }}
        >
          🔄 Reset to Defaults
        </Button>
      </div>

      {/* Preset Modal */}
      <Modal
        isOpen={showPresetModal}
        onClose={() => setShowPresetModal(false)}
        title="Save Configuration Preset"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Preset Name
            </label>
            <input
              type="text"
              placeholder="e.g., High Performance Setup"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={presetName}
              onChange={(e) => setPresetName(e.target.value)}
            />
          </div>
          <div className="flex gap-3">
            <Button
              variant="primary"
              className="flex-1"
              onClick={handleSavePreset}
              disabled={!presetName.trim()}
            >
              Save
            </Button>
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => {
                setShowPresetModal(false);
                setPresetName('');
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
