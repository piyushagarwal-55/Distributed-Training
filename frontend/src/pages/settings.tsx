import React, { useState, useEffect } from 'react';
import { useConfigStore, useTrainingStore } from '@/lib/store';

export default function SettingsPage() {
  const { config, updateConfig, presets, loadPreset } = useConfigStore();
  const { startTraining } = useTrainingStore();
  const [localConfig, setLocalConfig] = useState(config);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setLocalConfig(config);
  }, [config]);

  const handleSave = () => {
    updateConfig(localConfig);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleStartTraining = () => {
    updateConfig(localConfig);
    startTraining();
  };

  if (!localConfig?.training) {
    return <div className="p-6 text-gray-500">Loading configuration...</div>;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Settings</h1>
          <p className="text-sm text-gray-500 mt-1">Configure training parameters</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleSave} className="btn btn-secondary">
            {saved ? 'Saved!' : 'Save'}
          </button>
          <button onClick={handleStartTraining} className="btn btn-primary">
            Start Training
          </button>
        </div>
      </div>

      {/* Presets */}
      <div className="card p-5">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Quick Presets</h3>
        <div className="flex flex-wrap gap-2">
          {presets.map((p) => (
            <button key={p.name} onClick={() => loadPreset(p.name)} className="btn btn-sm btn-secondary">
              {p.name}
            </button>
          ))}
        </div>
      </div>

      {/* Training Parameters */}
      <div className="card p-5">
        <h3 className="text-sm font-medium text-gray-900 mb-4">Training Parameters</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="label">Model Type</label>
            <select
              className="input"
              value={localConfig.training.model_type}
              onChange={(e) => setLocalConfig({ ...localConfig, training: { ...localConfig.training, model_type: e.target.value } })}
            >
              <option value="simple_cnn">Simple CNN</option>
              <option value="resnet">ResNet</option>
              <option value="vgg">VGG</option>
              <option value="transformer">Transformer</option>
            </select>
          </div>
          <div>
            <label className="label">Dataset</label>
            <select
              className="input"
              value={localConfig.training.dataset}
              onChange={(e) => setLocalConfig({ ...localConfig, training: { ...localConfig.training, dataset: e.target.value } })}
            >
              <option value="MNIST">MNIST</option>
              <option value="CIFAR-10">CIFAR-10</option>
              <option value="CIFAR-100">CIFAR-100</option>
              <option value="ImageNet">ImageNet</option>
            </select>
          </div>
          <div>
            <label className="label">Epochs</label>
            <input
              type="number"
              className="input"
              value={localConfig.training.epochs}
              onChange={(e) => setLocalConfig({ ...localConfig, training: { ...localConfig.training, epochs: parseInt(e.target.value) || 1 } })}
              min={1}
              max={1000}
            />
          </div>
          <div>
            <label className="label">Batch Size</label>
            <select
              className="input"
              value={localConfig.training.batch_size}
              onChange={(e) => setLocalConfig({ ...localConfig, training: { ...localConfig.training, batch_size: parseInt(e.target.value) } })}
            >
              <option value={16}>16</option>
              <option value={32}>32</option>
              <option value={64}>64</option>
              <option value={128}>128</option>
              <option value={256}>256</option>
            </select>
          </div>
          <div>
            <label className="label">Learning Rate</label>
            <select
              className="input"
              value={localConfig.training.learning_rate}
              onChange={(e) => setLocalConfig({ ...localConfig, training: { ...localConfig.training, learning_rate: parseFloat(e.target.value) } })}
            >
              <option value={0.1}>0.1</option>
              <option value={0.01}>0.01</option>
              <option value={0.001}>0.001</option>
              <option value={0.0001}>0.0001</option>
            </select>
          </div>
          <div>
            <label className="label">Optimizer</label>
            <select
              className="input"
              value={localConfig.training.optimizer}
              onChange={(e) => setLocalConfig({ ...localConfig, training: { ...localConfig.training, optimizer: e.target.value } })}
            >
              <option value="adam">Adam</option>
              <option value="sgd">SGD</option>
              <option value="rmsprop">RMSprop</option>
              <option value="adamw">AdamW</option>
            </select>
          </div>
        </div>
      </div>

      {/* Network Settings */}
      <div className="card p-5">
        <h3 className="text-sm font-medium text-gray-900 mb-4">Network Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="label">Node Count</label>
            <input
              type="number"
              className="input"
              value={localConfig.nodes.count}
              onChange={(e) => setLocalConfig({ ...localConfig, nodes: { ...localConfig.nodes, count: parseInt(e.target.value) || 1 } })}
              min={1}
              max={100}
            />
          </div>
          <div>
            <label className="label">Network Profile</label>
            <select
              className="input"
              value={localConfig.network.profile}
              onChange={(e) => setLocalConfig({ ...localConfig, network: { ...localConfig.network, profile: e.target.value } })}
            >
              <option value="perfect">Perfect</option>
              <option value="good">Good</option>
              <option value="average">Average</option>
              <option value="poor">Poor</option>
            </select>
          </div>
          <div>
            <label className="label">Adaptive Scaling</label>
            <select
              className="input"
              value={localConfig.nodes.adaptive_enabled ? 'enabled' : 'disabled'}
              onChange={(e) => setLocalConfig({ ...localConfig, nodes: { ...localConfig.nodes, adaptive_enabled: e.target.value === 'enabled' } })}
            >
              <option value="enabled">Enabled</option>
              <option value="disabled">Disabled</option>
            </select>
          </div>
        </div>
      </div>

      {/* Blockchain Settings */}
      <div className="card p-5">
        <h3 className="text-sm font-medium text-gray-900 mb-4">Blockchain Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">RPC Endpoint</label>
            <input
              type="text"
              className="input font-mono text-sm"
              value={localConfig.blockchain.rpc_endpoint}
              onChange={(e) => setLocalConfig({ ...localConfig, blockchain: { ...localConfig.blockchain, rpc_endpoint: e.target.value } })}
            />
          </div>
          <div>
            <label className="label">Reward Pool (ETH)</label>
            <input
              type="number"
              step="0.01"
              className="input"
              value={localConfig.blockchain.reward_pool}
              onChange={(e) => setLocalConfig({ ...localConfig, blockchain: { ...localConfig.blockchain, reward_pool: parseFloat(e.target.value) || 0 } })}
              min={0}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
