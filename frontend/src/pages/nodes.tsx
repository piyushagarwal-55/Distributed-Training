import React from 'react';
import { useNodeStore } from '@/lib/store';

export default function NodesPage() {
  const { nodes, addNode } = useNodeStore();

  const handleAddDemoNode = () => {
    addNode({
      id: `node-${Date.now()}`,
      status: 'online',
      health: 'healthy',
      gpu: { model: 'RTX 4090', memory: 24, utilization: Math.random() * 100 },
      network: { latency: Math.floor(Math.random() * 50) + 10, bandwidth: 1000 },
    });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Nodes</h1>
          <p className="text-gray-500 mt-1">Manage your compute nodes</p>
        </div>
        <button onClick={handleAddDemoNode} className="btn btn-primary">
          Add Node
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="stat-card">
          <p className="stat-label">Total Nodes</p>
          <p className="stat-value">{nodes.length}</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Online</p>
          <p className="stat-value text-green-600">{nodes.filter(n => n.status === 'online').length}</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Avg Latency</p>
          <p className="stat-value">
            {nodes.length ? Math.round(nodes.reduce((a, n) => a + (n.network?.latency || 0), 0) / nodes.length) : 0}ms
          </p>
        </div>
      </div>

      {/* Nodes List */}
      <div className="card">
        {nodes.length === 0 ? (
          <div className="p-12 text-center">
            <p className="text-gray-400">No nodes configured</p>
            <button onClick={handleAddDemoNode} className="btn btn-secondary mt-4">
              Add Demo Node
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {nodes.map((node) => (
              <div key={node.id} className="p-4 flex items-center justify-between hover:bg-slate-50">
                <div className="flex items-center gap-4">
                  <div className={`w-2.5 h-2.5 rounded-full ${node.status === 'online' ? 'bg-green-500' : 'bg-gray-300'}`} />
                  <div>
                    <p className="font-medium text-sm">{node.id}</p>
                    <p className="text-xs text-gray-500">{node.gpu?.model || 'Unknown GPU'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-6 text-sm">
                  <div className="text-right">
                    <p className="text-gray-500 text-xs">Memory</p>
                    <p className="font-medium">{node.gpu?.memory || 0} GB</p>
                  </div>
                  <div className="text-right">
                    <p className="text-gray-500 text-xs">Latency</p>
                    <p className="font-medium">{node.network?.latency || 0}ms</p>
                  </div>
                  <span className={`badge ${node.status === 'online' ? 'badge-success' : 'badge-neutral'}`}>
                    {node.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
