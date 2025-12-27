import React, { useState } from 'react';
import { useConfigStore, useTrainingStore } from '@/lib/store';

export default function SettingsPage() {
  const { config, updateConfig, presets, loadPreset } = useConfigStore();
  const { startTraining } = useTrainingStore();
  const [localConfig, setLocalConfig] = useState(config);

  React.useEffect(() => {
    setLocalConfig(config);
  }, [config]);

  const handleSave = () => {
    updateConfig(localConfig);
  };

  const handleStartTraining = () => {
    updateConfig(localConfig);
    startTraining();
  };

  if (!localConfig?.training) {
    return <div className="p-6">Loading...</div>;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500 mt-1">Configure training parameters</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleSave} className="btn btn-secondary">Save</button>
          <button onClick={handleStartTraining} className="btn btn-primary">Start Training</button>
        </div>
      </div>

      {/* Presets */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Presets</h3>
        <div className="flex gap-2">
          {presets.map((p) => (
            <button key={p.name} onClick={() => loadPreset(p.name)} className="btn btn-secondary text-xs">
              {p.name}
            </button>
          ))}
        </div>
      </div>

      {/* Training Config */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Training Parameters</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="label">Model Type</label>
            <select
              className="input"
              value={localConfig.training.model_type}
              onChange={(e) => setLocalConfig({
                ...localConfig,
                training: { ...localConfig.training, model_type: e.target.value }
              })}
            >
              <option value="simple_cnn">Simple CNN</option>
              <option value="resnet">ResNet</option>
              <option value="vgg">VGG</option>
            </select>
          </div>
          <div>
            <label className="label">Dataset</label>
            <select
              className="input"
              value={localConfig.training.dataset}
              onChange={(e) => setLocalConfig({
                ...localConfig,
                training: { ...localConfig.training, dataset: e.target.value }
              })}
            >
              <option value="MNIST">MNIST</option>
              <option value="CIFAR-10">CIFAR-10</option>
              <option value="ImageNet">ImageNet</option>
            </select>
          </div>
          <div>
            <label className="label">Epochs</label>
            <input
              type="number"
              className="input"
              value={localConfig.training.epochs}
              onChange={(e) => setLocalConfig({
                ...localConfig,
                training: { ...localConfig.training, epochs: parseInt(e.target.value) }
              })}
            />
          </div>
          <div>
            <label className="label">Batch Size</label>
            <input
              type="number"
              className="input"
              value={localConfig.training.batch_size}
              onChange={(e) => setLocalConfig({
                ...localConfig,
                training: { ...localConfig.training, batch_size: parseInt(e.target.value) }
              })}
            />
          </div>
          <div>
            <label className="label">Learning Rate</label>
            <input
              type="number"
              step="0.0001"
              className="input"
              value={localConfig.training.learning_rate}
              onChange={(e) => setLocalConfig({
                ...localConfig,
                training: { ...localConfig.training, learning_rate: parseFloat(e.target.value) }
              })}
            />
          </div>
          <div>
            <label className="label">Optimizer</label>
            <select
              className="input"
              value={localConfig.training.optimizer}
              onChange={(e) => setLocalConfig({
                ...localConfig,
                training: { ...localConfig.training, optimizer: e.target.value }
              })}
            >
              <option value="adam">Adam</option>
              <option value="sgd">SGD</option>
              <option value="rmsprop">RMSprop</option>
            </select>
          </div>
        </div>
      </div>

      {/* Network Config */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Network Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="label">Node Count</label>
            <input
              type="number"
              className="input"
              value={localConfig.nodes.count}
              onChange={(e) => setLocalConfig({
                ...localConfig,
                nodes: { ...localConfig.nodes, count: parseInt(e.target.value) }
              })}
            />
          </div>
          <div>
            <label className="label">Network Profile</label>
            <select
              className="input"
              value={localConfig.network.profile}
              onChange={(e) => setLocalConfig({
                ...localConfig,
                network: { ...localConfig.network, profile: e.target.value }
              })}
            >
              <option value="good">Good</option>
              <option value="average">Average</option>
              <option value="poor">Poor</option>
            </select>
          </div>
          <div>
            <label className="label">Reward Pool (ETH)</label>
            <input
              type="number"
              step="0.01"
              className="input"
              value={localConfig.blockchain.reward_pool}
              onChange={(e) => setLocalConfig({
                ...localConfig,
                blockchain: { ...localConfig.blockchain, reward_pool: parseFloat(e.target.value) }
              })}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
