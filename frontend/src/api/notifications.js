import client from './client';

export const notificationsAPI = {
  list: async () => {
    const res = await client.get('/notifications/');
    return res.data;
  },
  unreadCount: async () => {
    const res = await client.get('/notifications/unread-count');
    return res.data.count;
  },
  markAllRead: async () => {
    const res = await client.post('/notifications/mark-read');
    return res.data;
  },
};
