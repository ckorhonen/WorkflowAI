import { PaymentMethodResponse, TenantData } from '@/types/workflowAI';
import { AddPaymentMethodContent } from './AddPaymentMethodContent';
import { AmountToAddSection } from './AmountToAddSection';
import { AutomaticPaymentsSection } from './AutomaticPaymentsSection';
import { BottomButtonBar } from './BottomButtonBar';
import { CreditBalanceSection } from './CreditBalanceSection';
import { EnableAutoRechargeContent } from './EnableAutoRechargeComponent';
import { InfoLabel } from './InfoLabel';
import { PaymentMethodSection } from './PaymentMethodSection';

type ManageCardsContentProps = {
  isPaymentMethodAvailable: boolean;
  organizationSettings: TenantData;
  paymentMethod: PaymentMethodResponse | undefined;
  balance: number | undefined;
  onAddCredits: () => void;
  setShowAddPaymentMethod: (show: boolean) => void;
  setIsOpen: (open: boolean) => void;
  showAddPaymentMethod: boolean;
  showEnableAutoRecharge: boolean;
  setShowEnableAutoRecharge: (show: boolean) => void;
  amountToAdd: number | undefined;
  setAmountToAdd: (amount: number | undefined) => void;
  isAddCreditsButtonActive: boolean;
  deletePaymentMethod: () => Promise<void>;
  automaticPaymentsFailure: string | undefined;
};

export function ManageCardsContent(props: ManageCardsContentProps) {
  const {
    isPaymentMethodAvailable,
    organizationSettings,
    paymentMethod,
    balance,
    onAddCredits,
    setShowAddPaymentMethod,
    setIsOpen,
    showAddPaymentMethod,
    showEnableAutoRecharge,
    setShowEnableAutoRecharge,
    amountToAdd,
    setAmountToAdd,
    isAddCreditsButtonActive,
    deletePaymentMethod,
    automaticPaymentsFailure,
  } = props;

  if (showAddPaymentMethod) {
    return <AddPaymentMethodContent setIsOpen={() => setShowAddPaymentMethod(false)} />;
  }

  if (showEnableAutoRecharge) {
    return (
      <EnableAutoRechargeContent
        organizationSettings={organizationSettings}
        setIsOpen={() => setShowEnableAutoRecharge(false)}
      />
    );
  }

  return (
    <div className='flex flex-col h-full w-full overflow-hidden bg-custom-gradient-1 rounded-[2px]'>
      <div className='text-[16px] font-semibold text-gray-900 px-4 py-3.5 border-b border-gray-200 border-dashed'>
        Add to Credits Balance
      </div>
      {!isPaymentMethodAvailable && (
        <InfoLabel text='Set up a payment method to start adding credits to your account.' />
      )}
      {balance !== undefined && <CreditBalanceSection balance={balance} />}
      <PaymentMethodSection
        paymentMethod={paymentMethod}
        addPaymentMethod={() => setShowAddPaymentMethod(true)}
        deletePaymentMethod={deletePaymentMethod}
      />
      <AmountToAddSection amountToAdd={amountToAdd} setAmountToAdd={setAmountToAdd} />
      <AutomaticPaymentsSection
        hasPaymentMethod={isPaymentMethodAvailable}
        automaticPaymentsFailure={automaticPaymentsFailure}
        organizationSettings={organizationSettings}
        onEnableAutoRecharge={() => setShowEnableAutoRecharge(true)}
      />
      <BottomButtonBar
        tooltipText={!isPaymentMethodAvailable ? 'Add a Payment method before adding credits' : undefined}
        actionText='Add Credits'
        isActionDisabled={!isAddCreditsButtonActive}
        onCancel={() => setIsOpen(false)}
        onAction={onAddCredits}
      />
    </div>
  );
}
