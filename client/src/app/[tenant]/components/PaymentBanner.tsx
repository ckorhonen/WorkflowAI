import { WarningRegular } from '@fluentui/react-icons';
import { useCallback, useMemo } from 'react';
import { Button } from '@/components/ui/Button';
import { useRedirectWithParams } from '@/lib/queryString';
import { PaymentBannerType } from './usePaymentBanners';

type PaymentBannerProps = {
  state: PaymentBannerType;
};

export function PaymentBanner(props: PaymentBannerProps) {
  const { state } = props;

  const redirectWithParams = useRedirectWithParams();

  const onOpenPayments = useCallback(() => {
    redirectWithParams({
      params: {
        manageCards: 'true',
      },
    });
  }, [redirectWithParams]);

  const texts = useMemo(() => {
    switch (state) {
      case PaymentBannerType.FIX_PAYMENT:
        return {
          mainText: 'Auto-Recharge payment failed.',
          secondaryText: 'Update your billing info now to keep your account active.',
          buttonText: 'Fix Payment',
        };
      case PaymentBannerType.ADD_CREDITS:
        return {
          mainText: 'Low Credit Balance.',
          secondaryText: 'Add credits to avoid runs being disabled.',
          buttonText: 'Add Credits',
        };
    }
  }, [state]);

  return (
    <div className='flex flex-row gap-2 w-full bg-red-100 text-white justify-center items-center h-11 px-4 flex-shrink-0'>
      <WarningRegular className='w-4 h-4 text-red-600' />
      <div className='text-red-600 text-[13px] font-semibold pr-1'>
        {texts.mainText} <span className='font-normal'>{texts.secondaryText}</span>
      </div>
      <Button onClick={onOpenPayments} variant='destructive' size='sm'>
        {texts.buttonText}
      </Button>
    </div>
  );
}
