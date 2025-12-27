import React from 'react';
import Link from 'next/link';
import { useTrainingStore, useNodeStore, useBlockchainStore } from '@/lib/store';

export default function HomePage() {
  const { session, isTraining, metrics } = useTrainingStore();
  const { nodes } = useNodeStore();
  const { isConnected, connect } = useBlockchainStore();

  const onlineNodes = nodes.filter(n => n.status === 'online').length;
  const latestMetric = metrics[metrics.length - 1];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Monitor your distributed training network</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Status</p>
              <p className="stat-value">{isTraining ? 'Training' : 'Idle'}</p>
            </div>
            <div className={`w-3 h-3 rounded-full ${isTraining ? 'bg-green-500' : 'bg-gray-300'}`} />
          </div>
        </div>

        <div className="stat-card">
          <p className="stat-label">Active Nodes</p>
          <p className="stat-value">{onlineNodes}<span className="text-lg text-gray-400">/{nodes.length}</span></p>
        </div>

        <div className="stat-card">
          <p className="stat-label">Accuracy</p>
          <p className="stat-value">
            {latestMetric ? `${(latestMetric.accuracy * 100).toFixed(1)}%` : '—'}
          </p>
        </div>

        <div className="stat-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="stat-label">Blockchain</p>
              <p className="stat-value text-lg">{isConnected ? 'Connected' : 'Offline'}</p>
            </div>
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-300'}`} />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Link href="/training" className="btn btn-primary justify-center">
            Start Training
          </Link>
          <Link href="/nodes" className="btn btn-secondary justify-center">
            Manage Nodes
          </Link>
          <button 
            onClick={() => connect()} 
            className="btn btn-secondary justify-center"
            disabled={isConnected}
          >
            {isConnected ? 'Connected' : 'Connect Wallet'}
          </button>
          <Link href="/settings" className="btn btn-secondary justify-center">
            Settings
          </Link>
        </div>
      </div>

      {/* Current Session */}
      {session && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-900">Current Session</h2>
            <span className={`badge ${session.status === 'running' ? 'badge-success' : 'badge-warning'}`}>
              {session.status}
            </span>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Model</p>
              <p className="font-medium">{session.modelName || 'CNN'}</p>
            </div>
            <div>
              <p className="text-gray-500">Dataset</p>
              <p className="font-medium">{session.dataset || 'MNIST'}</p>
            </div>
            <div>
              <p className="text-gray-500">Progress</p>
              <p className="font-medium">{session.currentEpoch} / {session.totalEpochs} epochs</p>
            </div>
            <div>
              <p className="text-gray-500">Loss</p>
              <p className="font-medium">{latestMetric?.loss.toFixed(4) || '—'}</p>
            </div>
          </div>
          {/* Progress bar */}
          <div className="mt-4">
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-indigo-600 transition-all duration-300"
                style={{ width: `${(session.currentEpoch / session.totalEpochs) * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Network Info */}
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-gray-900 mb-4">Network</h2>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="p-4 bg-slate-50 rounded-lg">
            <p className="text-xs text-gray-500 mb-1">Chain</p>
            <p className="font-medium">Monad Testnet</p>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg">
            <p className="text-xs text-gray-500 mb-1">Chain ID</p>
            <p className="font-mono text-sm">10143</p>
          </div>
          <div className="p-4 bg-slate-50 rounded-lg">
            <p className="text-xs text-gray-500 mb-1">RPC</p>
            <p className="font-mono text-xs truncate">testnet-rpc.monad.xyz</p>
          </div>
        </div>
      </div>
    </div>
  );
}
