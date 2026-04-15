import client from './client';

export const authAPI = {
  register: async (email, username, password) => {
    const response = await client.post('/auth/register', { email, username, password });
    return response.data;
  },

  login: async (email, password) => {
    const response = await client.post('/auth/login', { email, password });
    return response.data;
  },

  getProfile: async () => {
    const response = await client.get('/users/me');
    return response.data;
  },

  getProfileWithStats: async () => {
    const response = await client.get('/users/me/stats');
    return response.data;
  },

  logout: async () => {
    const response = await client.post('/auth/logout');
    return response.data;
  },

  refreshToken: async (refreshToken) => {
    const response = await client.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },

  sendVerificationCode: async () => {
    const response = await client.post('/auth/send-verification-code');
    return response.data;
  },

  verifyCode: async (code) => {
    const response = await client.post('/auth/verify-code', { code });
    return response.data;
  },

  addEmail: async (email) => {
    const response = await client.post('/auth/add-email', { email });
    return response.data;
  },
};
