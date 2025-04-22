import { ArrowUp } from 'lucide-react';
import { formatFractionalCurrency } from '@/lib/formatters/numberFormatters';
import { cn } from '@/lib/utils';

type StatsPriceProps = {
  price: number | undefined;
  bestPrice: number | undefined;
};

export function StatsPrice(props: StatsPriceProps) {
  const { price, bestPrice } = props;

  const isBest = price === bestPrice;
  const text = formatFractionalCurrency(price) ?? '-';

  const worserText = bestPrice && price && bestPrice < price ? `${(price / bestPrice).toFixed(1)}x` : undefined;

  if (!price) {
    return <div className='flex items-center justify-start w-full h-full text-gray-500 text-[16px]'>-</div>;
  }

  return (
    <div className='flex items-center justify-start w-full h-full text-gray-500 text-[13px]'>
      {worserText && (
        <span className='flex flex-row items-center text-[13px] font-medium text-red-500 mr-2'>
          {worserText}
          <ArrowUp size={12} />
        </span>
      )}
      <span
        className={cn(
          isBest
            ? 'text-green-700 font-medium bg-green-50 border-green-200 border rounded-[2px] px-[6px] py-[1px]'
            : 'text-gray-500 font-medium'
        )}
      >
        {text}
      </span>
    </div>
  );
}
