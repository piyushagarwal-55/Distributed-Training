import React from 'react';
import Link from 'next/link';
import { useTrainingStore, useNodeStore, useBlockchainStore } from '@/lib/store';

export default function HomePage() {
  const { session, isTraining, metrics } = useTrainingStore();
  const { nodes } = useNodeStore();
  const { isConnected, contributions, connect } = useBlockchainStore();

  const onlineNodes = nodes.filter(n => n.status === 'online').length;
  const latestMetric = metrics[metrics.length - 1];
  const progress = session ? (session.currentEpoch / session.totalEpochs) * 100 : 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Overview of your distributed training network</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card">
          <p className="stat-label">Status</p>
          <div className="flex items-center gap-2 mt-1">
            <span className={`status-dot ${isTraining ? 'status-online animate-pulse-slow' : 'status-offline'}`} />
            <span className="stat-value text-xl">{isTraining ? 'Training' : 'Idle'}</span>
          </div>
        </div>

        <div className="stat-card">
          <p className="stat-label">Active Nodes</p>
          <p className="stat-value">
            {onlineNodes}
            <span className="text-base font-normal text-gray-400 ml-1">/ {nodes.length}</span>
          </p>
        </div>

        <div className="stat-card">
          <p className="stat-label">Accuracy</p>
          <p className="stat-value">
            {latestMetric ? `${(latestMetric.accuracy * 100).toFixed(1)}%` : '—'}
          </p>
        </div>

        <div className="stat-card">
          <p className="stat-label">Contributions</p>
          <p className="stat-value">{contributions.length}</p>
        </div>
      </div>

      {/* Training Progress */}
      {session && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-medium text-gray-900">Training Progress</h2>
              <p className="text-xs text-gray-500 mt-0.5">{session.modelName} on {session.dataset}</p>
            </div>
            <span className={`badge ${session.status === 'running' ? 'badge-success' : 'badge-warning'}`}>
              {session.status}
            </span>
          </div>
          
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Epoch {session.currentEpoch} of {session.totalEpochs}</span>
              <span className="font-medium">{progress.toFixed(0)}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
          </div>

          {latestMetric && (
            <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-100">
              <div>
                <p className="text-xs text-gray-500">Loss</p>
                <p className="text-sm font-medium">{latestMetric.loss.toFixed(4)}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Accuracy</p>
                <p className="text-sm font-medium">{(latestMetric.accuracy * 100).toFixed(1)}%</p>
              </div>
              <div>
                <p className="text-xs text-gray-500">Step</p>
                <p className="text-sm font-medium">{latestMetric.step}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Quick Actions */}
      <div className="card p-5">
        <h2 className="text-sm font-medium text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Link href="/training" className="btn btn-primary">
            Start Training
          </Link>
          <Link href="/nodes" className="btn btn-secondary">
            Manage Nodes
          </Link>
          <button 
            onClick={() => connect()} 
            className="btn btn-secondary"
            disabled={isConnected}
          >
            {isConnected ? 'Connected' : 'Connect Wallet'}
          </button>
          <Link href="/blockchain" className="btn btn-secondary">
            View Rewards
          </Link>
        </div>
      </div>

      {/* Network Info */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Nodes Overview */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-gray-900">Nodes</h2>
            <Link href="/nodes" className="text-xs text-gray-500 hover:text-gray-700">View all</Link>
          </div>
          {nodes.length === 0 ? (
            <p className="text-sm text-gray-400 py-4 text-center">No nodes connected</p>
          ) : (
            <div className="space-y-2">
              {nodes.slice(0, 3).map((node) => (
                <div key={node.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className={`status-dot ${node.status === 'online' ? 'status-online' : node.status === 'busy' ? 'status-busy' : 'status-offline'}`} />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{node.id}</p>
                      <p className="text-xs text-gray-500">{node.gpu?.model || 'Unknown'}</p>
                    </div>
                  </div>
                  <span className={`badge ${node.status === 'online' ? 'badge-success' : node.status === 'busy' ? 'badge-warning' : 'badge-neutral'}`}>
                    {node.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Chain Info */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-gray-900">Blockchain</h2>
            <div className="flex items-center gap-1.5">
              <span className={`status-dot ${isConnected ? 'status-online' : 'status-offline'}`} />
              <span className="text-xs text-gray-500">{isConnected ? 'Connected' : 'Offline'}</span>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-500">Network</span>
              <span className="text-sm font-medium">Monad Testnet</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-500">Chain ID</span>
              <span className="text-sm font-mono">10143</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-500">Contributions</span>
              <span className="text-sm font-medium">{contributions.length}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
