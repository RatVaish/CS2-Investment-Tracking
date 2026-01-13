import client from './client';

export const investmentsAPI = {
  // Get all investments
  getAll: async () => {
    const response = await client.get('/investments/');
    return response.data;
  },

  // Get single investment
  getById: async (id) => {
    const response = await client.get(`/investments/${id}`);
    return response.data;
  },

  // Create new investment
  create: async (investmentData) => {
    const response = await client.post('/investments/', investmentData);
    return response.data;
  },

  // Update investment
  update: async (id, investmentData) => {
    const response = await client.patch(`/investments/${id}`, investmentData);
    return response.data;
  },

  // Delete investment
  delete: async (id) => {
    const response = await client.delete(`/investments/${id}`);
    return response.data;
  },

  // Refresh single price
  refreshPrice: async (id) => {
    const response = await client.post(`/prices/refresh/${id}`);
    return response.data;
  },

  // Refresh all prices
  refreshAllPrices: async () => {
    const response = await client.post('/prices/refresh-all');
    return response.data;
  }
};