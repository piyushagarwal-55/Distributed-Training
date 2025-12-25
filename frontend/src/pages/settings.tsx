import React from 'react';
import { ConfigurationPanel } from '@/components/organisms/ConfigurationPanel';

export default function SettingsPage() {
  console.log('[SettingsPage] Rendering');
  
  return (
    <div className="p-6">
      <ConfigurationPanel />
    </div>
  );
}
