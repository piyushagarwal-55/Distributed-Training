import React from 'react';
import { clsx } from 'clsx';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'neutral' | 'accent';
  size?: 'sm' | 'md' | 'lg';
  dot?: boolean;
  pulse?: boolean;
}

export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ children, variant = 'neutral', size = 'md', dot = false, pulse = false, className, ...props }, ref) => {
    const variantStyles = {
      primary: 'bg-primary-100 text-primary-700 border-primary-200',
      success: 'bg-success-100 text-success-700 border-success-200',
      warning: 'bg-warning-100 text-warning-700 border-warning-200',
      danger: 'bg-red-100 text-red-700 border-red-200',
      neutral: 'bg-gray-100 text-gray-700 border-gray-200',
      accent: 'bg-accent-100 text-accent-700 border-accent-200',
    };

    const sizeStyles = {
      sm: 'px-2 py-0.5 text-xs rounded-md',
      md: 'px-2.5 py-1 text-sm rounded-lg',
      lg: 'px-3 py-1.5 text-base rounded-lg',
    };

    const dotColors = {
      primary: 'bg-primary-500',
      success: 'bg-success-500',
      warning: 'bg-warning-500',
      danger: 'bg-red-500',
      neutral: 'bg-gray-500',
      accent: 'bg-accent-500',
    };

    return (
      <span
        ref={ref}
        className={clsx(
          'inline-flex items-center font-medium border',
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {dot && (
          <span
            className={clsx(
              'w-2 h-2 rounded-full mr-1.5',
              dotColors[variant],
              pulse && 'animate-pulse'
            )}
          />
        )}
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';
