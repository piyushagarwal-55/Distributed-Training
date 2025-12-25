import React from 'react';
import { Card } from '../atoms/Card';
import { Badge } from '../atoms/Badge';

export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  icon?: string;
  variant?: 'default' | 'purple' | 'green' | 'blue' | 'yellow' | 'success' | 'warning' | 'danger';
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  trend,
  trendValue,
  icon,
  variant = 'default',
  className = '',
}) => {
  console.log('[MetricCard] Rendering:', { title, value, trend });

  const variantStyles = {
    default: 'border-gray-200 bg-white',
    purple: 'border-primary-200 bg-primary-50',
    green: 'border-success-200 bg-success-50',
    blue: 'border-accent-200 bg-accent-50',
    yellow: 'border-warning-200 bg-warning-50',
    success: 'border-success-200 bg-success-50',
    warning: 'border-warning-200 bg-warning-50',
    danger: 'border-red-200 bg-red-50',
  };

  const textColorStyles = {
    default: 'text-gray-900',
    purple: 'text-primary-700',
    green: 'text-success-700',
    blue: 'text-accent-700',
    yellow: 'text-warning-700',
    success: 'text-success-700',
    warning: 'text-warning-700',
    danger: 'text-red-700',
  };

  const trendIcons = {
    up: '↗',
    down: '↘',
    neutral: '→',
  };

  const trendColors = {
    up: 'text-emerald-600',
    down: 'text-red-600',
    neutral: 'text-gray-600',
  };

  return (
    <Card className={`${variantStyles[variant]} ${className} rounded-xl`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-600 mb-1 font-medium">{title}</p>
          <div className="flex items-baseline gap-2">
            {icon && <span className="text-2xl">{icon}</span>}
            <h3 className={`text-3xl font-bold ${textColorStyles[variant]}`}>{value}</h3>
          </div>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        {trend && trendValue && (
          <div className={`flex items-center gap-1 text-sm ${trendColors[trend]}`}>
            <span className="text-lg">{trendIcons[trend]}</span>
            <span className="font-semibold">{trendValue}</span>
          </div>
        )}
      </div>
    </Card>
  );
};
