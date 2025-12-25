import React from 'react';
import { TrainingDashboard } from '@/components/organisms/TrainingDashboard';

export default function TrainingPage() {
  console.log('[TrainingPage] Rendering');
  
  return (
    <div className="p-6">
      <TrainingDashboard />
    </div>
  );
}
