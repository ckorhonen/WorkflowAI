import { CheckmarkCircleRegular, DismissCircleRegular } from '@fluentui/react-icons';
import { Button } from '@/components/ui/Button';
import { TenantData } from '@/types/workflowAI';
import { PaymentsFailedInfoLabel } from './PaymentsFailedInfoLabel';

type AutomaticPaymentsSectionProps = {
  automaticPaymentsFailure: string | undefined;
  hasPaymentMethod: boolean;
  organizationSettings: Pick<
    TenantData,
    'automatic_payment_enabled' | 'automatic_payment_threshold' | 'automatic_payment_balance_to_maintain'
  >;
  onEnableAutoRecharge: () => void;
  onUpdatePaymentMethod: () => void;
};

function EnabledAutomaticPaymentsSection(
  props: Pick<AutomaticPaymentsSectionProps, 'organizationSettings' | 'onEnableAutoRecharge'>
) {
  const { organizationSettings, onEnableAutoRecharge } = props;

  return (
    <div className='flex flex-col'>
      <div className='flex flex-row items-center gap-1'>
        <CheckmarkCircleRegular className='text-green-500 w-4 h-4' />
        <div className='text-gray-700 font-normal text-[13px]'>
          Auto recharge is <span className='font-semibold'>on</span>.
        </div>
      </div>
      <div className='text-gray-500 font-normal text-[12px] pt-1'>
        When your credit balance reaches ${organizationSettings.automatic_payment_threshold}, your payment method will
        be charged to bring the balance up to ${organizationSettings.automatic_payment_balance_to_maintain}.
      </div>
      <div className='pt-2'>
        <Button variant='newDesignGray' onClick={onEnableAutoRecharge}>
          Modify Auto-Recharge
        </Button>
      </div>
    </div>
  );
}

export function AutomaticPaymentsSection(props: AutomaticPaymentsSectionProps) {
  const {
    organizationSettings,
    onEnableAutoRecharge,
    automaticPaymentsFailure,
    hasPaymentMethod,
    onUpdatePaymentMethod,
  } = props;

  const isAutomaticPaymentsEnabled = organizationSettings.automatic_payment_enabled;

  return (
    <div className='flex flex-col px-4 py-2 gap-1'>
      <div className='text-gray-900 font-medium text-[13px]'>Automatic Payments</div>
      {automaticPaymentsFailure && (
        <PaymentsFailedInfoLabel
          className='py-3 flex w-full whitespace-pre-line'
          onUpdatePaymentMethod={onUpdatePaymentMethod}
        />
      )}
      {isAutomaticPaymentsEnabled && !automaticPaymentsFailure ? (
        <EnabledAutomaticPaymentsSection
          organizationSettings={organizationSettings}
          onEnableAutoRecharge={onEnableAutoRecharge}
        />
      ) : (
        <div className='flex flex-col'>
          <div className='flex flex-row items-center gap-1'>
            <DismissCircleRegular className='text-gray-400 w-4 h-4' />
            <div className='text-gray-700 font-normal text-[13px]'>
              Auto recharge is <span className='font-semibold'>off</span>.
            </div>
          </div>
          <div className='text-gray-500 font-normal text-[12px] pt-1'>
            {hasPaymentMethod
              ? 'Enable automatic recharge to automatically keep your credit balance topped up.'
              : 'Set up a payment method to enable automatic recharge.'}
          </div>

          <div className='pt-2'>
            <Button variant='newDesignIndigo' onClick={onEnableAutoRecharge} disabled={!hasPaymentMethod}>
              Enable Auto-Recharge
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
