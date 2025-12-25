import React from 'react';
import { clsx } from 'clsx';

export interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'neutral';
  className?: string;
}

export const Spinner: React.FC<SpinnerProps> = ({ size = 'md', color = 'primary', className }) => {
  const sizeStyles = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  };

  const colorStyles = {
    primary: 'text-primary-500',
    success: 'text-success-500',
    warning: 'text-warning-500',
    danger: 'text-danger-500',
    neutral: 'text-neutral-500',
  };

  return (
    <div className={clsx('inline-block', className)}>
      <svg
        className={clsx('animate-spin', sizeStyles[size], colorStyles[color])}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
  );
};

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  width?: string | number;
  height?: string | number;
  circle?: boolean;
  count?: number;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width,
  height = '1rem',
  circle = false,
  count = 1,
  className,
  ...props
}) => {
  const skeletons = Array.from({ length: count }, (_, i) => (
    <div
      key={i}
      className={clsx(
        'animate-pulse bg-neutral-200',
        circle ? 'rounded-full' : 'rounded',
        className
      )}
      style={{
        width: width || (circle ? height : '100%'),
        height,
      }}
      {...props}
    />
  ));

  return count > 1 ? <div className="space-y-2">{skeletons}</div> : skeletons[0];
};

export interface LoadingOverlayProps {
  visible: boolean;
  message?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  visible,
  message = 'Loading...',
  size = 'lg',
}) => {
  if (!visible) return null;

  return (
    <div className="fixed inset-0 bg-neutral-900/50 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-card p-6 rounded-lg shadow-xl text-center">
        <Spinner size={size} />
        <p className="mt-4 text-neutral-700 font-medium">{message}</p>
      </div>
    </div>
  );
};
