import React, { useState, useRef, useEffect } from 'react';

export interface TooltipProps {
  content: string;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delay?: number;
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  position = 'top',
  delay = 300,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();

  console.log('[Tooltip] Rendering:', { content, position, delay });

  const handleMouseEnter = () => {
    console.log('[Tooltip] Mouse enter');
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true);
      if (triggerRef.current) {
        const rect = triggerRef.current.getBoundingClientRect();
        setCoords({ x: rect.left + rect.width / 2, y: rect.top });
        console.log('[Tooltip] Position calculated:', { x: rect.left, y: rect.top });
      }
    }, delay);
  };

  const handleMouseLeave = () => {
    console.log('[Tooltip] Mouse leave');
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsVisible(false);
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const positionStyles: Record<string, string> = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  return (
    <div className="relative inline-block" ref={triggerRef}>
      <div
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
      >
        {children}
      </div>
      {isVisible && (
        <div
          className={`
            absolute z-50 px-3 py-2 text-sm text-white bg-gray-800 rounded-lg
            whitespace-nowrap pointer-events-none
            ${positionStyles[position]}
            animate-fade-in
          `}
        >
          {content}
          <div
            className={`
              absolute w-2 h-2 bg-gray-800 rotate-45
              ${position === 'top' ? 'bottom-[-4px] left-1/2 -translate-x-1/2' : ''}
              ${position === 'bottom' ? 'top-[-4px] left-1/2 -translate-x-1/2' : ''}
              ${position === 'left' ? 'right-[-4px] top-1/2 -translate-y-1/2' : ''}
              ${position === 'right' ? 'left-[-4px] top-1/2 -translate-y-1/2' : ''}
            `}
          />
        </div>
      )}
    </div>
  );
};
