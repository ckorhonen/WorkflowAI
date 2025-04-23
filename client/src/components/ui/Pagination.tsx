import { ChevronLeft16Filled, ChevronRight16Filled } from '@fluentui/react-icons';
import * as React from 'react';
import { cn } from '@/lib/utils/cn';

const Pagination = ({ className, ...props }: React.ComponentProps<'nav'>) => (
  <nav
    role='navigation'
    aria-label='pagination'
    className={cn('mx-auto flex w-full justify-center', className)}
    {...props}
  />
);
Pagination.displayName = 'Pagination';

const PaginationContent = React.forwardRef<HTMLUListElement, React.ComponentProps<'ul'>>(
  ({ className, ...props }, ref) => (
    <ul ref={ref} className={cn('flex flex-row items-center gap-1', className)} {...props} />
  )
);
PaginationContent.displayName = 'PaginationContent';

const PaginationItem = React.forwardRef<HTMLLIElement, React.ComponentProps<'li'>>(({ className, ...props }, ref) => (
  <li ref={ref} className={cn('', className)} {...props} />
));
PaginationItem.displayName = 'PaginationItem';

type PaginationLinkProps = {
  isActive?: boolean;
} & React.ComponentProps<'a'>;

const PaginationLink = ({ className, isActive, ...props }: PaginationLinkProps) => (
  <a
    aria-current={isActive ? 'page' : undefined}
    className={cn('flex items-center justify-center px-1.5 min-h-7 min-w-7', className)}
    {...props}
  />
);
PaginationLink.displayName = 'PaginationLink';

type PaginationNavigationProps = {
  showLabel?: boolean;
} & React.ComponentProps<typeof PaginationLink>;

const PaginationPrevious = ({ className, showLabel, ...props }: PaginationNavigationProps) => (
  <PaginationLink
    aria-label='Go to previous page'
    className={cn('flex items-center justify-center h-7', showLabel ? 'px-2' : 'w-7', 'mr-1', className)}
    {...props}
  >
    <ChevronLeft16Filled className='h-4 w-4' />
    {showLabel && <span className='ml-1'>Previous</span>}
  </PaginationLink>
);
PaginationPrevious.displayName = 'PaginationPrevious';

const PaginationNext = ({ className, showLabel, ...props }: PaginationNavigationProps) => (
  <PaginationLink
    aria-label='Go to next page'
    className={cn('flex items-center justify-center h-7', showLabel ? 'px-2' : 'w-7', 'ml-1', className)}
    {...props}
  >
    {showLabel && <span className='mr-1'>Next</span>}
    <ChevronRight16Filled className='h-4 w-4' />
  </PaginationLink>
);
PaginationNext.displayName = 'PaginationNext';

const PaginationEllipsis = ({ className, ...props }: React.ComponentProps<'span'>) => (
  <span aria-hidden className={cn('flex h-7 w-7 items-center justify-center', className)} {...props}>
    <div className='font-lato font-semibold text-sm text-gray-900'>...</div>
    <span className='sr-only'>More pages</span>
  </span>
);
PaginationEllipsis.displayName = 'PaginationEllipsis';

export {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
};
