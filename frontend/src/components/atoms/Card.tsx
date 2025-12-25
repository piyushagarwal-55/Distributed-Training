import React from 'react';
import { clsx } from 'clsx';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  padding?: 'none' | 'sm' | 'md' | 'lg';
  elevated?: boolean;
  variant?: 'default' | 'purple' | 'green' | 'blue' | 'yellow';
}

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export interface CardBodyProps extends React.HTMLAttributes<HTMLDivElement> {
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  divided?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ children, padding = 'md', elevated = true, variant = 'default', className, ...props }, ref) => {
    const paddingStyles = {
      none: 'p-0',
      sm: 'p-3',
      md: 'p-4',
      lg: 'p-6',
    };

    const variantStyles = {
      default: 'bg-white border-gray-200',
      purple: 'bg-primary-50 border-primary-100',
      green: 'bg-success-50 border-success-100',
      blue: 'bg-accent-50 border-accent-100',
      yellow: 'bg-warning-50 border-warning-100',
    };

    return (
      <div
        ref={ref}
        className={clsx(
          'rounded-xl border',
          variantStyles[variant],
          elevated && 'shadow-sm hover:shadow-md transition-all duration-200',
          paddingStyles[padding],
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = 'Card';

export const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ title, subtitle, action, children, className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx('flex items-start justify-between mb-4', className)}
        {...props}
      >
        <div className="flex-1">
          {title && <h3 className="text-lg font-semibold text-neutral-900">{title}</h3>}
          {subtitle && <p className="text-sm text-neutral-600 mt-1">{subtitle}</p>}
          {children}
        </div>
        {action && <div className="ml-4">{action}</div>}
      </div>
    );
  }
);

CardHeader.displayName = 'CardHeader';

export const CardBody = React.forwardRef<HTMLDivElement, CardBodyProps>(
  ({ children, padding = 'none', className, ...props }, ref) => {
    const paddingStyles = {
      none: 'p-0',
      sm: 'p-3',
      md: 'p-4',
      lg: 'p-6',
    };

    return (
      <div
        ref={ref}
        className={clsx(paddingStyles[padding], className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardBody.displayName = 'CardBody';

export const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ children, divided = true, className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'mt-4 pt-4',
          divided && 'border-t border-neutral-200',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardFooter.displayName = 'CardFooter';
