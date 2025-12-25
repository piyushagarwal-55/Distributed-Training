import React from 'react';

export interface AlertProps {
  type?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  message: string;
  onClose?: () => void;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  type = 'info',
  title,
  message,
  onClose,
  className = '',
}) => {
  console.log('[Alert] Rendering:', { type, title, message });

  const typeStyles = {
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    warning: 'bg-orange-50 border-orange-200 text-orange-800',
    error: 'bg-red-50 border-red-200 text-red-800',
  };

  const iconStyles = {
    info: '🔵',
    success: '✅',
    warning: '⚠️',
    error: '❌',
  };

  return (
    <div
      className={`
        ${typeStyles[type]}
        border rounded-lg p-4 mb-4
        ${className}
      `}
      role="alert"
    >
      <div className="flex items-start">
        <div className="flex-shrink-0 text-xl mr-3">
          {iconStyles[type]}
        </div>
        <div className="flex-1">
          {title && (
            <h3 className="text-sm font-semibold mb-1">{title}</h3>
          )}
          <p className="text-sm">{message}</p>
        </div>
        {onClose && (
          <button
            onClick={() => {
              console.log('[Alert] Close clicked');
              onClose();
            }}
            className="flex-shrink-0 ml-3 text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
};
