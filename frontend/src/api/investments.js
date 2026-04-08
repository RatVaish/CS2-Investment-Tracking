import client from './client';

export const investmentsAPI = {
  getAll: (status = null) => {
    const params = status ? { status } : {};
    return client.get('/investments/', { params }).then(r => r.data);
  },

  getById: (id) =>
    client.get(`/investments/${id}`).then(r => r.data),

  getByItem: (itemId) =>
    client.get(`/investments/by-item/${itemId}`).then(r => r.data),

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

  getBackfillStatus: (itemId) =>
    client.get(`/portfolio/backfill-status/${itemId}`).then(r => r.data),
};

export const importAPI = {
  getSteamInventory: () =>
    client.get('/import/steam-inventory').then(r => r.data),

  importSteamItems: (items) =>
    client.post('/import/steam-inventory', { items }).then(r => r.data),

  importCSV: (file) => {
    const form = new FormData();
    form.append('file', file);
    return client.post('/import/csv', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data);
  },

  getCSVTemplate: () =>
    client.get('/import/csv/template', { responseType: 'blob' }).then(r => r.data),

  exportCSV: (status = 'active') =>
    client.get('/portfolio/export/csv', {
      params: { status },
      responseType: 'blob',
    }).then(r => r.data),
};

export const snapshotsAPI = {
  getSnapshots: (days = 90) =>
    client.get('/portfolio/snapshots', { params: { days } }).then(r => r.data),

  triggerSnapshot: () =>
    client.post('/portfolio/snapshots/trigger').then(r => r.data),
};

export const predictionAPI = {
  predictEntryDate: (itemId, month, year, purchasePrice) =>
    client.get(`/portfolio/predict-entry-date/${itemId}`, {
      params: { month, year, purchase_price: purchasePrice },
    }).then(r => r.data),
};
