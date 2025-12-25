import React, { useState, useEffect } from 'react';
import { Card } from '../atoms/Card';
import { Badge } from '../atoms/Badge';
import { Button } from '../atoms/Button';
import { Table } from '../atoms/Table';
import { Tooltip } from '../atoms/Tooltip';
import { useBlockchainStore } from '../../lib/store';
import { formatTime, formatNumber } from '../../utils/dateFormat';

export const BlockchainDashboard: React.FC = () => {
  const {
    isConnected,
    blockNumber,
    contributions,
    rewards,
    transactions,
    connect,
    claimReward,
  } = useBlockchainStore();

  console.log('[BlockchainDashboard] Rendering:', {
    isConnected,
    blockNumber,
    contributionsCount: contributions.length,
    transactionsCount: transactions.length,
  });

  const contributionColumns = [
    {
      key: 'nodeId',
      label: 'Node ID',
      render: (contrib: any) => (
        <span className="font-mono text-sm">{contrib.nodeId}</span>
      ),
    },
    {
      key: 'computeTime',
      label: 'Compute Time',
      render: (contrib: any) => `${contrib.computeTime}s`,
    },
    {
      key: 'gradientsAccepted',
      label: 'Gradients',
      render: (contrib: any) => contrib.gradientsAccepted,
    },
    {
      key: 'qualityScore',
      label: 'Quality Score',
      render: (contrib: any) => (
        <div className="flex items-center gap-2">
          <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500"
              style={{ width: `${(contrib.qualityScore / 10000) * 100}%` }}
            />
          </div>
          <span className="text-sm">{contrib.qualityScore}/10000</span>
        </div>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (contrib: any) => (
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            console.log('[BlockchainDashboard] View on explorer:', contrib.txHash);
            window.open(`https://explorer.monad.xyz/tx/${contrib.txHash}`, '_blank');
          }}
        >
          View on Explorer
        </Button>
      ),
    },
  ];

  const rewardColumns = [
    {
      key: 'nodeId',
      label: 'Node ID',
      render: (reward: any) => (
        <span className="font-mono text-sm">{reward.nodeId}</span>
      ),
    },
    {
      key: 'amount',
      label: 'Amount',
      render: (reward: any) => (
        <span className="font-semibold text-blue-600">
          {(parseFloat(reward.amount) / 1e18).toFixed(4)} ETH
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (reward: any) => (
        <Badge variant={reward.claimed ? 'success' : 'warning'}>
          {reward.claimed ? 'Claimed' : 'Pending'}
        </Badge>
      ),
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (reward: any) => (
        !reward.claimed && (
          <Button
            size="sm"
            variant="success"
            onClick={() => {
              console.log('[BlockchainDashboard] Claim reward:', reward.nodeId);
              claimReward(reward.nodeId);
            }}
          >
            Claim
          </Button>
        )
      ),
    },
  ];

  const transactionColumns = [
    {
      key: 'hash',
      label: 'Transaction Hash',
      render: (tx: any) => (
        <Tooltip content={tx.hash}>
          <span className="font-mono text-sm">{tx.hash.slice(0, 10)}...{tx.hash.slice(-8)}</span>
        </Tooltip>
      ),
    },
    {
      key: 'type',
      label: 'Type',
      render: (tx: any) => (
        <Badge variant="neutral">{tx.type}</Badge>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (tx: any) => {
        const variants: Record<string, 'success' | 'warning' | 'danger'> = {
          confirmed: 'success',
          pending: 'warning',
          failed: 'danger',
        };
        return <Badge variant={variants[tx.status]}>{tx.status}</Badge>;
      },
    },
    {
      key: 'gasUsed',
      label: 'Gas Used',
      render: (tx: any) => formatNumber(tx.gasUsed, 'N/A'),
    },
    {
      key: 'timestamp',
      label: 'Time',
      render: (tx: any) => formatTime(tx.timestamp),
    },
  ];

  // Calculate stats
  const totalContributions = contributions.length;
  const totalRewards = rewards.reduce((sum, r) => sum + parseFloat(r.amount), 0) / 1e18;
  const pendingRewards = rewards.filter(r => !r.claimed).length;
  const confirmedTx = transactions.filter(tx => tx.status === 'confirmed').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Blockchain Dashboard</h1>
          <p className="text-gray-600 mt-1">
            On-chain contributions and rewards
          </p>
        </div>
        {!isConnected ? (
          <Button
            variant="primary"
            onClick={() => {
              console.log('[BlockchainDashboard] Connect clicked');
              connect();
            }}
          >
            🔗 Connect to Blockchain
          </Button>
        ) : (
          <Badge variant="success">Connected</Badge>
        )}
      </div>

      {/* Connection Status */}
      <Card className="bg-blue-50 border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 mb-1">Connection Status</p>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-gray-400'}`} />
              <span className="font-semibold">
                {isConnected ? 'Connected to Monad' : 'Disconnected'}
              </span>
            </div>
          </div>
          {isConnected && (
            <div className="text-right">
              <p className="text-sm text-gray-600">Current Block</p>
              <p className="text-xl font-bold text-blue-600">#{blockNumber}</p>
            </div>
          )}
        </div>
      </Card>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <p className="text-sm text-gray-600 mb-1">Total Contributions</p>
          <p className="text-3xl font-bold text-gray-900">{totalContributions}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-600 mb-1">Total Rewards</p>
          <p className="text-3xl font-bold text-emerald-600">{totalRewards.toFixed(4)} ETH</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-600 mb-1">Pending Claims</p>
          <p className="text-3xl font-bold text-orange-600">{pendingRewards}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-600 mb-1">Confirmed Transactions</p>
          <p className="text-3xl font-bold text-blue-600">{confirmedTx}</p>
        </Card>
      </div>

      {/* Contributions Table */}
      <Card>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Recorded Contributions</h2>
          <Button
            size="sm"
            variant="outline"
            onClick={() => console.log('[BlockchainDashboard] Export contributions')}
          >
            📊 Export
          </Button>
        </div>
        <Table
          data={contributions}
          columns={contributionColumns}
          sortable
        />
      </Card>

      {/* Rewards Tracker */}
      <Card>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Rewards Tracker</h2>
          <Button
            size="sm"
            variant="success"
            onClick={() => console.log('[BlockchainDashboard] Claim all rewards')}
            disabled={pendingRewards === 0}
          >
            💰 Claim All Pending
          </Button>
        </div>
        <Table
          data={rewards}
          columns={rewardColumns}
          sortable
        />
      </Card>

      {/* Reward Calculation Breakdown */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Reward Calculation</h2>
        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
            <span className="text-gray-700">Strategy:</span>
            <span className="font-semibold">Proportional Distribution</span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
            <span className="text-gray-700">Formula:</span>
            <span className="font-mono text-xs">
              reward = (nodeScore / totalScore) × rewardPool
            </span>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
            <span className="text-gray-700">Reward Pool:</span>
            <span className="font-semibold text-blue-600">0.1 ETH</span>
          </div>
        </div>
      </Card>

      {/* Transaction History */}
      <Card>
        <div className="mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Transaction History</h2>
        </div>
        <Table
          data={transactions}
          columns={transactionColumns}
          sortable
        />
      </Card>

      {/* Contract Information */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Contract Information</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-600 mb-1">Training Registry</p>
            <p className="font-mono text-xs bg-gray-50 p-2 rounded break-all">
              0x5FbDB2315678afecb367f032d93F642f64180aa3
            </p>
          </div>
          <div>
            <p className="text-gray-600 mb-1">Contribution Tracker</p>
            <p className="font-mono text-xs bg-gray-50 p-2 rounded break-all">
              0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512
            </p>
          </div>
          <div>
            <p className="text-gray-600 mb-1">Reward Distributor</p>
            <p className="font-mono text-xs bg-gray-50 p-2 rounded break-all">
              0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0
            </p>
          </div>
          <div>
            <p className="text-gray-600 mb-1">RPC Endpoint</p>
            <p className="font-mono text-xs bg-gray-50 p-2 rounded break-all">
              https://testnet-rpc.monad.xyz
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};
