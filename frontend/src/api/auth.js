import client from './client';

export const authAPI = {
  // Register new user
  register: async (email, username, password) => {
    const response = await client.post('/auth/register', {
      email,
      username,
      password
    });
    return response.data;
  },

  // Login
  login: async (email, password) => {
    const response = await client.post('/auth/login', {
      email,
      password
    });
    return response.data;
  },

  // Get current user profile
  getProfile: async () => {
    const response = await client.get('/users/me');
    return response.data;
  },

  // Get user profile with stats
  getProfileWithStats: async () => {
    const response = await client.get('/users/me/stats');
    return response.data;
  },

  // Logout (just returns success, actual logout is client-side)
  logout: async () => {
    const response = await client.post('/auth/logout');
    return response.data;
  },

  // Refresh access token
  refreshToken: async (refreshToken) => {
    const response = await client.post('/auth/refresh', {
      refresh_token: refreshToken
    });
    return response.data;
  }
};