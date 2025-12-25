import React, { useState } from 'react';

export interface Column<T = any> {
  key: string;
  label: string;
  render?: (item: T) => React.ReactNode;
  sortable?: boolean;
}

export interface TableProps<T = any> {
  data: T[];
  columns: Column<T>[];
  sortable?: boolean;
  emptyMessage?: string;
  onRowClick?: (item: T) => void;
}

export function Table<T = any>({
  data,
  columns,
  sortable = false,
  emptyMessage = 'No data available',
  onRowClick,
}: TableProps<T>) {
  const [sortKey, setSortKey] = useState<string>('');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  console.log('[Table] Rendering:', { dataCount: data.length, columnsCount: columns.length });

  const handleSort = (key: string) => {
    if (!sortable) return;
    
    console.log('[Table] Sort by:', key);
    
    if (sortKey === key) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDirection('asc');
    }
  };

  const sortedData = React.useMemo(() => {
    if (!sortKey || !sortable) return data;

    return [...data].sort((a: any, b: any) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [data, sortKey, sortDirection, sortable]);

  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={`
                  px-4 py-3 text-left text-sm font-semibold text-gray-700
                  ${sortable ? 'cursor-pointer hover:bg-gray-100' : ''}
                `}
                onClick={() => sortable && handleSort(column.key)}
              >
                <div className="flex items-center gap-2">
                  {column.label}
                  {sortable && sortKey === column.key && (
                    <span className="text-blue-600">
                      {sortDirection === 'asc' ? '↑' : '↓'}
                    </span>
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((item, index) => (
            <tr
              key={index}
              className={`
                border-b border-gray-100 hover:bg-gray-50 transition-colors
                ${onRowClick ? 'cursor-pointer' : ''}
              `}
              onClick={() => onRowClick?.(item)}
            >
              {columns.map((column) => (
                <td key={column.key} className="px-4 py-3 text-sm text-gray-900">
                  {column.render ? column.render(item) : String((item as any)[column.key] || '-')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
