import React from 'react';
import { Card } from '../atoms/Card';

export interface StatCardProps {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  color?: string;
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon,
  color = 'blue',
  className = '',
}) => {
  console.log('[StatCard] Rendering:', { label, value, color });

  return (
    <Card className={`p-4 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
        {icon && (
          <div className={`text-3xl text-${color}-600`}>
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
};
