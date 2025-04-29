import { useOrganizationSettings } from '@/store/organization_settings';

export enum PaymentBannerType {
  FIX_PAYMENT = 'FIX_PAYMENT',
  ADD_CREDITS = 'ADD_CREDITS',
}

export function usePaymentBanners(isSignedIn: boolean) {
  const organizationSettings = useOrganizationSettings((state) => state.settings);
  const lowCreditsMode = !!organizationSettings?.current_credits_usd && organizationSettings.current_credits_usd <= 5;
  const paymentFailure = !!organizationSettings?.payment_failure;

  if (!isSignedIn) {
    return {
      state: undefined,
    };
  }

  if (lowCreditsMode) {
    return {
      state: PaymentBannerType.ADD_CREDITS,
    };
  }

  if (paymentFailure) {
    return {
      state: PaymentBannerType.FIX_PAYMENT,
    };
  }

  return {
    state: undefined,
  };
}
