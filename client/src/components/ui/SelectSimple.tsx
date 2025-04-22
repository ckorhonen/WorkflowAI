import * as React from 'react';
import { cn } from '@/lib/utils/cn';

const SelectSimple = React.forwardRef<HTMLSelectElement, React.SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, ...props }, ref) => {
    return (
      <select
        className={cn(
          'flex h-10 w-full font-normal rounded-md border border-gray-200 border-input bg-background px-3 py-2 text-sm text-gray-900 ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-50',
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
SelectSimple.displayName = 'SelectSimple';

export { SelectSimple };
