import React from 'react';
import { BlockchainDashboard } from '@/components/organisms/BlockchainDashboard';

export default function BlockchainPage() {
  console.log('[BlockchainPage] Rendering');
  
  return (
    <div className="p-6">
      <BlockchainDashboard />
    </div>
  );
}
