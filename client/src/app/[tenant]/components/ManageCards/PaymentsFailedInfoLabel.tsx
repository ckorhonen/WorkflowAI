import { Info16Regular } from '@fluentui/react-icons';

type PaymentsFailedInfoLabelProps = {
  className?: string;
  onUpdatePaymentMethod: () => void;
};

export function PaymentsFailedInfoLabel(props: PaymentsFailedInfoLabelProps) {
  const { className = 'px-4 py-3 flex w-full', onUpdatePaymentMethod } = props;

  return (
    <div className={className}>
      <div className='flex flex-row w-full items-center bg-indigo-50 rounded-[2px] border border-indigo-300'>
        <Info16Regular className='text-indigo-700 w-4 h-4 mx-3 flex-shrink-0' />
        <div className='flex flex-col gap-4 text-[13px] font-normal text-indigo-700 pr-3 py-2'>
          <div>Auto Recharge payment failed because your payment method was declined.</div>
          <div className='flex flex-col gap-[2px]'>
            <div>To avoid running out of credits:</div>
            <div className='pl-2'>• Check if the credit card above is valid</div>
            <div className='pl-2 cursor-pointer' onClick={onUpdatePaymentMethod}>
              • <span className='underline'>Update the payment method, if needed</span>
            </div>
            <div className='pl-2'>• Then re-enable Auto Recharge</div>
          </div>
        </div>
      </div>
    </div>
  );
}
