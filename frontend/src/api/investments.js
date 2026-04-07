import client from './client';

export const investmentsAPI = {
  getAll: (status = null) => {
    const params = status ? { status } : {};
    return client.get('/investments/', { params }).then(r => r.data);
  },

  getById: (id) =>
    client.get(`/investments/${id}`).then(r => r.data),

  getSummary: () =>
    client.get('/investments/summary').then(r => r.data),

  create: (data) =>
    client.post('/investments/', data).then(r => r.data),

  update: (id, data) =>
    client.patch(`/investments/${id}`, data).then(r => r.data),

  sell: (id, soldPrice, soldFee = null) =>
    client.post(`/investments/${id}/sell`, { sold_price: soldPrice, sold_fee: soldFee }).then(r => r.data),

  delete: (id) =>
    client.delete(`/investments/${id}`).then(r => r.data),
};

export const portfolioAPI = {
  getSummary: () =>
    client.get('/portfolio/summary').then(r => r.data),

  getTopPerformers: (limit = 5) =>
    client.get('/portfolio/top-performers', { params: { limit } }).then(r => r.data),

  getPriceHistory: (itemId, market = 'steam', resolution = 'daily', days = null) => {
    const params = { market, resolution };
    if (days) params.days = days;
    return client.get(`/portfolio/price-history/${itemId}`, { params }).then(r => r.data);
  },

  getAvailableMarkets: (itemId) =>
    client.get(`/portfolio/available-markets/${itemId}`).then(r => r.data),
};
