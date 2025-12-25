import React, { useState } from 'react';
import { Card } from '../atoms/Card';
import { Badge } from '../atoms/Badge';
import { Button } from '../atoms/Button';
import { Table } from '../atoms/Table';
import { Modal } from '../atoms/Modal';
import { Tooltip } from '../atoms/Tooltip';
import { useNodeStore } from '../../lib/store';

export const NodeManagement: React.FC = () => {
  const { nodes, selectedNode, selectNode, updateNodeStatus } = useNodeStore();
  const [showDetailModal, setShowDetailModal] = useState(false);

  console.log('[NodeManagement] Rendering:', { nodeCount: nodes.length, selectedNode });

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'warning' | 'danger' | 'neutral'> = {
      online: 'success',
      degraded: 'warning',
      offline: 'danger',
    };
    return <Badge variant={variants[status] || 'neutral'}>{status.toUpperCase()}</Badge>;
  };

  const getHealthColor = (health: string) => {
    const colors: Record<string, string> = {
      healthy: 'text-emerald-600',
      degraded: 'text-orange-600',
      critical: 'text-red-600',
    };
    return colors[health] || 'text-gray-600';
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const columns = [
    {
      key: 'id',
      label: 'Node ID',
      render: (node: any) => (
        <Tooltip content={node.address}>
          <span className="font-mono text-sm">{node.id}</span>
        </Tooltip>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (node: any) => getStatusBadge(node.status),
    },
    {
      key: 'health',
      label: 'Health',
      render: (node: any) => (
        <span className={`font-semibold ${getHealthColor(node.health)}`}>
          {node.health}
        </span>
      ),
    },
    {
      key: 'latency',
      label: 'Latency',
      render: (node: any) => `${node.network?.latency || 0}ms`,
    },
    {
      key: 'uptime',
      label: 'Uptime',
      render: (node: any) => formatUptime(node.metrics?.uptime || 0),
    },
    {
      key: 'contribution',
      label: 'Contribution',
      render: (node: any) => {
        const score = node.contribution?.finalScore || 0;
        return (
          <div className="flex items-center gap-2">
            <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-600"
                style={{ width: `${Math.min(score * 100, 100)}%` }}
              />
            </div>
            <span className="text-sm">{(score * 100).toFixed(1)}%</span>
          </div>
        );
      },
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (node: any) => (
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              console.log('[NodeManagement] View details:', node.id);
              selectNode(node.id);
              setShowDetailModal(true);
            }}
          >
            View
          </Button>
          <Button
            size="sm"
            variant={node.status === 'online' ? 'danger' : 'success'}
            onClick={() => {
              console.log('[NodeManagement] Toggle node:', node.id);
              updateNodeStatus(node.id, node.status === 'online' ? 'offline' : 'online');
            }}
          >
            {node.status === 'online' ? 'Disable' : 'Enable'}
          </Button>
        </div>
      ),
    },
  ];

  // Calculate stats
  const onlineNodes = nodes.filter(n => n.status === 'online').length;
  const avgLatency = nodes.length > 0
    ? Math.round(nodes.reduce((sum, n) => sum + n.network.latency, 0) / nodes.length)
    : 0;
  const healthyNodes = nodes.filter(n => n.health === 'healthy').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Node Management</h1>
          <p className="text-gray-600 mt-1">
            Monitor and manage training nodes
          </p>
        </div>
        <Button
          variant="primary"
          onClick={() => console.log('[NodeManagement] Add node clicked')}
        >
          + Add Node
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <p className="text-sm text-gray-600 mb-1">Total Nodes</p>
          <p className="text-3xl font-bold text-gray-900">{nodes.length}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-600 mb-1">Online Nodes</p>
          <p className="text-3xl font-bold text-emerald-600">{onlineNodes}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-600 mb-1">Avg Latency</p>
          <p className="text-3xl font-bold text-blue-600">{avgLatency}ms</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-600 mb-1">Healthy Nodes</p>
          <p className="text-3xl font-bold text-green-600">{healthyNodes}</p>
        </Card>
      </div>

      {/* Nodes Table */}
      <Card>
        <div className="mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Active Nodes</h2>
        </div>
        <Table
          data={nodes}
          columns={columns}
          sortable
        />
      </Card>

      {/* Node Detail Modal */}
      {selectedNode && (
        <Modal
          isOpen={showDetailModal}
          onClose={() => {
            console.log('[NodeManagement] Close modal');
            setShowDetailModal(false);
          }}
          title={`Node Details: ${selectedNode.id}`}
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600">Status</p>
                <div className="mt-1">{getStatusBadge(selectedNode.status)}</div>
              </div>
              <div>
                <p className="text-sm text-gray-600">Health</p>
                <p className={`text-lg font-semibold mt-1 ${getHealthColor(selectedNode.health)}`}>
                  {selectedNode.health}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Address</p>
                <p className="text-sm font-mono mt-1 break-all">{selectedNode.address}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Latency</p>
                <p className="text-lg font-semibold mt-1">{selectedNode.network?.latency || 0}ms</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Uptime</p>
                <p className="text-lg font-semibold mt-1">{formatUptime(selectedNode.metrics?.uptime || 0)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Contribution Score</p>
                <p className="text-lg font-semibold mt-1">{((selectedNode.contribution?.finalScore || 0) * 100).toFixed(1)}%</p>
              </div>
            </div>
            
            <div className="pt-4 border-t border-gray-200">
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Recent Activity</h4>
              <div className="space-y-2 text-sm">
                <p className="text-gray-600">• Completed 150 training rounds</p>
                <p className="text-gray-600">• Submitted 145 gradients (96.7% acceptance)</p>
                <p className="text-gray-600">• Average computation time: 2.3s</p>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                variant="primary"
                className="flex-1"
                onClick={() => console.log('[NodeManagement] Health check:', selectedNode.id)}
              >
                Run Health Check
              </Button>
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => console.log('[NodeManagement] View logs:', selectedNode.id)}
              >
                View Logs
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Network Visualization Placeholder */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Network Topology</h2>
        <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center border border-gray-200">
          <p className="text-gray-500">Network visualization will appear here</p>
        </div>
      </Card>
    </div>
  );
};
