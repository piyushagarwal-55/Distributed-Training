import React from 'react';
import { NodeManagement } from '@/components/organisms/NodeManagement';

export default function NodesPage() {
  console.log('[NodesPage] Rendering');
  
  return (
    <div className="p-6">
      <NodeManagement />
    </div>
  );
}
