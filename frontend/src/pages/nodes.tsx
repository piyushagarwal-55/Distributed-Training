import React from 'react';
import { useNodeStore, Node } from '@/lib/store';

export default function NodesPage() {
  const { nodes, addNode, removeNode } = useNodeStore();

  const handleAddNode = () => {
    const gpus = ['NVIDIA RTX 4090', 'NVIDIA RTX 3090', 'NVIDIA RTX 3080', 'NVIDIA A100'];
    const randomGpu = gpus[Math.floor(Math.random() * gpus.length)];
    const memories: Record<string, number> = { 'NVIDIA RTX 4090': 24, 'NVIDIA RTX 3090': 24, 'NVIDIA RTX 3080': 10, 'NVIDIA A100': 80 };
    
    const newNode: Node = {
      id: `node-${nodes.length + 1}`,
      status: 'online',
      health: 'healthy',
      gpu: { 
        model: randomGpu, 
        memory: memories[randomGpu] * 1024, 
        utilization: Math.floor(Math.random() * 60) + 20 
      },
      network: { 
        latency: Math.floor(Math.random() * 30) + 10, 
        bandwidth: Math.floor(Math.random() * 500) + 500 
      },
      contribution: Math.floor(Math.random() * 100) + 50,
    };
    addNode(newNode);
  };

  const onlineNodes = nodes.filter(n => n.status === 'online').length;
  const totalMemory = nodes.reduce((acc, n) => acc + (n.gpu?.memory || 0), 0);
  const avgLatency = nodes.length ? Math.round(nodes.reduce((a, n) => a + (n.network?.latency || 0), 0) / nodes.length) : 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Nodes</h1>
          <p className="text-sm text-gray-500 mt-1">Manage compute nodes in your network</p>
        </div>
        <button onClick={handleAddNode} className="btn btn-primary">
          Add Node
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card">
          <p className="stat-label">Total Nodes</p>
          <p className="stat-value">{nodes.length}</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Online</p>
          <p className="stat-value text-emerald-600">{onlineNodes}</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Total Memory</p>
          <p className="stat-value">{(totalMemory / 1024).toFixed(0)} GB</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Avg Latency</p>
          <p className="stat-value">{avgLatency} ms</p>
        </div>
      </div>

      {/* Nodes List */}
      <div className="card">
        <div className="p-4 border-b border-gray-100">
          <h2 className="text-sm font-medium text-gray-900">All Nodes</h2>
        </div>
        
        {nodes.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
              </svg>
            </div>
            <p className="text-gray-500 mb-4">No nodes in your network</p>
            <button onClick={handleAddNode} className="btn btn-secondary">
              Add Your First Node
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {nodes.map((node) => (
              <div key={node.id} className="p-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                <div className="flex items-center gap-4">
                  <span className={`status-dot ${node.status === 'online' ? 'status-online' : node.status === 'busy' ? 'status-busy' : 'status-offline'}`} />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{node.id}</p>
                    <p className="text-xs text-gray-500">{node.gpu?.model || 'Unknown GPU'}</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-6">
                  <div className="hidden sm:block text-right">
                    <p className="text-xs text-gray-500">Memory</p>
                    <p className="text-sm font-medium">{((node.gpu?.memory || 0) / 1024).toFixed(0)} GB</p>
                  </div>
                  <div className="hidden sm:block text-right">
                    <p className="text-xs text-gray-500">Utilization</p>
                    <p className="text-sm font-medium">{node.gpu?.utilization?.toFixed(0) || 0}%</p>
                  </div>
                  <div className="hidden md:block text-right">
                    <p className="text-xs text-gray-500">Latency</p>
                    <p className="text-sm font-medium">{node.network?.latency || 0} ms</p>
                  </div>
                  <span className={`badge ${node.status === 'online' ? 'badge-success' : node.status === 'busy' ? 'badge-warning' : 'badge-neutral'}`}>
                    {node.status}
                  </span>
                  <button 
                    onClick={() => removeNode(node.id)}
                    className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
