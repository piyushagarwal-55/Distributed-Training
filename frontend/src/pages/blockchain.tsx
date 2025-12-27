import React from 'react';
import { useBlockchainStore } from '@/lib/store';

export default function BlockchainPage() {
  const { isConnected, account, balance, blockNumber, contributions, rewards, transactions, connect } = useBlockchainStore();

  const contracts = {
    registry: '0x8288000299F72407b63D9cC8eee8cDEfB4DB529f',
    tracker: '0xcE51Bc755396e63f849004580Ac37b7cfF616869',
    distributor: '0xd0C9942475FAA2738F1D75931a97ACD30d0C3833',
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Blockchain</h1>
          <p className="text-gray-500 mt-1">On-chain contributions and rewards</p>
        </div>
        {!isConnected && (
          <button onClick={() => connect()} className="btn btn-primary">
            Connect Wallet
          </button>
        )}
      </div>

      {/* Connection Status */}
      <div className="card p-5">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-300'}`} />
          <span className="font-medium">{isConnected ? 'Connected to Monad Testnet' : 'Not Connected'}</span>
        </div>
        {isConnected && account && (
          <div className="mt-4 grid grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="text-gray-500 text-xs">Account</p>
              <p className="font-mono text-xs truncate">{account}</p>
            </div>
            <div>
              <p className="text-gray-500 text-xs">Balance</p>
              <p className="font-medium">{balance} MON</p>
            </div>
            <div>
              <p className="text-gray-500 text-xs">Block</p>
              <p className="font-medium">#{blockNumber}</p>
            </div>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card">
          <p className="stat-label">Contributions</p>
          <p className="stat-value">{contributions.length}</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Total Rewards</p>
          <p className="stat-value text-green-600">
            {(rewards.reduce((a, r) => a + parseFloat(r.amount), 0) / 1e18).toFixed(4)}
          </p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Pending Claims</p>
          <p className="stat-value">{rewards.filter(r => !r.claimed).length}</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Transactions</p>
          <p className="stat-value">{transactions.length}</p>
        </div>
      </div>

      {/* Contracts */}
      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Deployed Contracts</h3>
        <div className="space-y-3">
          {Object.entries(contracts).map(([name, address]) => (
            <div key={name} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <span className="text-sm font-medium capitalize">{name.replace(/([A-Z])/g, ' $1')}</span>
              <code className="text-xs text-gray-600 font-mono">{address}</code>
            </div>
          ))}
        </div>
      </div>

      {/* Contributions */}
      {contributions.length > 0 && (
        <div className="card">
          <div className="p-4 border-b border-gray-100">
            <h3 className="text-sm font-semibold text-gray-900">Recent Contributions</h3>
          </div>
          <div className="divide-y divide-gray-100">
            {contributions.map((c, i) => (
              <div key={i} className="p-4 flex items-center justify-between">
                <div>
                  <p className="font-medium text-sm">{c.nodeId}</p>
                  <p className="text-xs text-gray-500">{c.gradientsAccepted} gradients</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{c.qualityScore}/10000</p>
                  <p className="text-xs text-gray-500">Quality Score</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
