import client from './client';

export const alertsAPI = {
  list: async () => {
    const res = await client.get('/alerts/');
    return res.data;
  },
  create: async (data) => {
    const res = await client.post('/alerts/', data);
    return res.data;
  },
  delete: async (id) => {
    const res = await client.delete(`/alerts/${id}`);
    return res.data;
  },
};
