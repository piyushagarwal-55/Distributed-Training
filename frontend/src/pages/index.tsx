import React from 'react';
import Link from 'next/link';
import { Card } from '@/components/atoms/Card';
import { Button } from '@/components/atoms/Button';
import { MetricCard } from '@/components/molecules/MetricCard';
import { useTrainingStore, useNodeStore, useBlockchainStore } from '@/lib/store';
import { formatTime } from '@/utils/dateFormat';

export default function HomePage() {
  const { session, isTraining, metrics } = useTrainingStore();
  const { nodes } = useNodeStore();
  const { isConnected } = useBlockchainStore();
  
  console.log('[HomePage] Rendering:', { session, isTraining, nodeCount: nodes.length });

  const onlineNodes = nodes.filter(n => n.status === 'online').length;
  const latestMetric = metrics[metrics.length - 1];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gray-900">
          Distributed Training Dashboard
        </h1>
        <p className="text-gray-600 mt-2">
          Monitor and manage your distributed machine learning training
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Training Status"
          value={isTraining ? 'Running' : 'Idle'}
          icon={isTraining ? '🟢' : '⚪'}
          variant={isTraining ? 'success' : 'purple'}
        />
        <MetricCard
          title="Active Nodes"
          value={`${onlineNodes} / ${nodes.length}`}
          icon="🖥️"
          variant="blue"
        />
        <MetricCard
          title="Current Accuracy"
          value={latestMetric ? `${(latestMetric.accuracy * 100).toFixed(2)}%` : 'N/A'}
          icon="🎯"
          variant="green"
        />
        <MetricCard
          title="Blockchain"
          value={isConnected ? 'Connected' : 'Disconnected'}
          icon="⛓️"
          variant={isConnected ? 'green' : 'yellow'}
        />
      </div>

      {/* Quick Actions */}
      <Card variant="default">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Link href="/training">
            <Button variant="primary" className="w-full">
              🚀 Training
            </Button>
          </Link>
          <Link href="/nodes">
            <Button variant="secondary" className="w-full">
              🖥️ Nodes
            </Button>
          </Link>
          <Link href="/blockchain">
            <Button variant="secondary" className="w-full">
              ⛓️ Blockchain
            </Button>
          </Link>
          <Link href="/settings">
            <Button variant="secondary" className="w-full">
              ⚙️ Settings
            </Button>
          </Link>
        </div>
      </Card>

      {/* Recent Session */}
      <Card variant="default">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Session</h2>
        <div className="space-y-3">
          {session ? (
            <div>
              <div className="flex items-center justify-between p-3 bg-gradient-to-r from-primary-50 to-primary-100 rounded-xl border border-primary-200">
                <div>
                  <p className="font-semibold text-gray-900">{session.id}</p>
                  <p className="text-sm text-gray-600">
                    Epoch {session.currentEpoch} / {session.totalEpochs}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-primary-600">{session.status}</p>
                  <p className="text-xs text-gray-500">
                    {formatTime(session.startTime)}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No active sessions</p>
          )}
        </div>
      </Card>

      <Card variant="default">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Node Status</h2>
        <div className="space-y-3">
          {nodes.slice(0, 3).map((node) => (
            <div key={node.id} className="flex items-center justify-between p-3 bg-gradient-to-r from-success-50 to-success-100 rounded-xl border border-success-200">
              <div>
                <p className="font-semibold text-gray-900">{node.id}</p>
                <p className="text-sm text-gray-600">{node.network?.latency || 0}ms latency</p>
              </div>
              <div className="text-right">
                <p className={`text-sm font-semibold ${
                  node.status === 'online' ? 'text-success-600' : 'text-gray-400'
                }`}>
                  {node.status}
                </p>
                <p className="text-xs text-gray-500">{node.health || 'unknown'}</p>
              </div>
            </div>
          ))}
          {nodes.length === 0 && (
            <p className="text-gray-500 text-center py-8">No nodes configured</p>
          )}
        </div>
      </Card>

      {/* System Info */}
      <Card variant="purple" className="border-primary-200">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-primary-700 mb-1">
              System Ready
            </h3>
            <p className="text-sm text-gray-600">
              All components initialized. Configure your training session to get started.
            </p>
          </div>
          <Link href="/settings">
            <Button variant="primary">
              Configure Training →
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
