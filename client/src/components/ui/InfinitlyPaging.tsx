import { cx } from 'class-variance-authority';
import { useCallback } from 'react';
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/Pagination';

type InfinitlyPagingProps = {
  currentPage: number;
  onPageSelected: (index: number) => void;
  nextPageAvailable: boolean;
  className?: string;
};

export function InfinitlyPaging(props: InfinitlyPagingProps) {
  const { currentPage, onPageSelected, nextPageAvailable, className } = props;

  const onPreviousePage = useCallback(() => {
    const newPage = currentPage - 1;
    if (newPage >= 0) {
      onPageSelected(newPage);
    }
  }, [currentPage, onPageSelected]);

  const onNextPage = useCallback(() => {
    const newPage = currentPage + 1;
    if (newPage >= 0) {
      onPageSelected(newPage);
    }
  }, [currentPage, onPageSelected]);

  const shouldShowPreviouse = currentPage > 0;
  const shouldShowNext = nextPageAvailable;

  const getItemClassName = (isActive: boolean, isDisabled?: boolean) =>
    cx('rounded-[2px]', {
      'bg-gray-200 border border-gray-300 shadow-inner hover:bg-gray-200 cursor-pointer': isActive && !isDisabled,
      'bg-white shadow-sm border border-gray-200 hover:bg-gray-100 cursor-pointer': !isActive && !isDisabled,
      'bg-gray-100/60 text-gray-300': isDisabled,
    });

  return (
    <div className={cx('flex w-full', className)}>
      <Pagination className='text-gray-800 font-lato text-xs font-semibold items-start justify-center'>
        <PaginationContent>
          {shouldShowPreviouse && (
            <PaginationItem>
              <PaginationPrevious
                onClick={onPreviousePage}
                className={getItemClassName(false, currentPage === 0)}
                showLabel
              />
            </PaginationItem>
          )}
          {shouldShowNext && (
            <PaginationItem>
              <PaginationNext onClick={onNextPage} className={getItemClassName(false, !nextPageAvailable)} showLabel />
            </PaginationItem>
          )}
        </PaginationContent>
      </Pagination>
    </div>
  );
}
