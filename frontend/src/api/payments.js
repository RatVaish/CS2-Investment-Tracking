import client from './client';

export const paymentsAPI = {
  getStatus: () =>
    client.get('/payments/status').then(r => r.data),

  createCheckoutSession: (priceId) =>
    client.post('/payments/create-checkout-session', {
      price_id: priceId,
      success_url: `${window.location.origin}/app/billing?success=true`,
      cancel_url: `${window.location.origin}/app/billing?canceled=true`,
    }).then(r => r.data),

  getBillingPortal: () =>
    client.get('/payments/billing-portal').then(r => r.data),
};
