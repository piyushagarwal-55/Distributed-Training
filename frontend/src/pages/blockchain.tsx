import React from 'react';
import { useBlockchainStore } from '@/lib/store';

export default function BlockchainPage() {
  const { isConnected, account, balance, blockNumber, contributions, rewards, transactions, connect, claimReward } = useBlockchainStore();

  const contracts = [
    { name: 'Training Registry', address: '0x8288000299F72407b63D9cC8eee8cDEfB4DB529f' },
    { name: 'Contribution Tracker', address: '0xcE51Bc755396e63f849004580Ac37b7cfF616869' },
    { name: 'Reward Distributor', address: '0xd0C9942475FAA2738F1D75931a97ACD30d0C3833' },
  ];

  const totalRewards = rewards.reduce((a, r) => a + parseFloat(r.amount), 0) / 1e18;
  const pendingClaims = rewards.filter(r => !r.claimed).length;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Blockchain</h1>
          <p className="text-sm text-gray-500 mt-1">On-chain contributions and rewards</p>
        </div>
        {!isConnected && (
          <button onClick={() => connect()} className="btn btn-primary">Connect Wallet</button>
        )}
      </div>

      <div className="card p-5">
        <div className="flex items-center gap-3 mb-4">
          <span className={`status-dot ${isConnected ? 'status-online' : 'status-offline'}`} style={{ width: 10, height: 10 }} />
          <span className="font-medium text-gray-900">{isConnected ? 'Connected to Monad Testnet' : 'Not Connected'}</span>
        </div>
        {isConnected && account && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">Account</p>
              <p className="text-sm font-mono truncate">{account}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">Balance</p>
              <p className="text-sm font-medium">{parseFloat(balance).toLocaleString()} MON</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-xs text-gray-500 mb-1">Block</p>
              <p className="text-sm font-medium">#{blockNumber.toLocaleString()}</p>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="stat-card"><p className="stat-label">Contributions</p><p className="stat-value">{contributions.length}</p></div>
        <div className="stat-card"><p className="stat-label">Total Rewards</p><p className="stat-value text-emerald-600">{totalRewards.toFixed(4)}</p></div>
        <div className="stat-card"><p className="stat-label">Pending Claims</p><p className="stat-value">{pendingClaims}</p></div>
        <div className="stat-card"><p className="stat-label">Transactions</p><p className="stat-value">{transactions.length}</p></div>
      </div>

      <div className="card p-5">
        <h3 className="text-sm font-medium text-gray-900 mb-4">Deployed Contracts</h3>
        <div className="space-y-2">
          {contracts.map((c) => (
            <div key={c.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">{c.name}</span>
              <code className="text-xs text-gray-500 font-mono">{c.address}</code>
            </div>
          ))}
        </div>
      </div>

      {rewards.length > 0 && (
        <div className="card">
          <div className="p-4 border-b border-gray-100"><h3 className="text-sm font-medium text-gray-900">Rewards</h3></div>
          <div className="divide-y divide-gray-100">
            {rewards.map((r, i) => (
              <div key={i} className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{r.nodeId}</p>
                  <p className="text-xs text-gray-500">{(parseFloat(r.amount) / 1e18).toFixed(6)} MON</p>
                </div>
                {r.claimed ? <span className="badge badge-success">Claimed</span> : <button onClick={() => claimReward(r.nodeId)} className="btn btn-sm btn-primary">Claim</button>}
              </div>
            ))}
          </div>
        </div>
      )}

      {contributions.length > 0 && (
        <div className="card">
          <div className="p-4 border-b border-gray-100"><h3 className="text-sm font-medium text-gray-900">Contributions</h3></div>
          <div className="divide-y divide-gray-100">
            {contributions.map((c, i) => (
              <div key={i} className="p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{c.nodeId}</p>
                    <p className="text-xs text-gray-500">{c.gradientsAccepted} gradients</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{(c.qualityScore / 100).toFixed(0)}%</p>
                  <p className="text-xs text-gray-500">Quality</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {transactions.length > 0 && (
        <div className="card">
          <div className="p-4 border-b border-gray-100"><h3 className="text-sm font-medium text-gray-900">Transactions</h3></div>
          <div className="divide-y divide-gray-100">
            {transactions.map((tx, i) => (
              <div key={i} className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{tx.type}</p>
                  <p className="text-xs text-gray-500 font-mono">{tx.hash}</p>
                </div>
                <span className={`badge ${tx.status === 'confirmed' ? 'badge-success' : tx.status === 'pending' ? 'badge-warning' : 'badge-error'}`}>{tx.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
