import client from './client';

export const itemsAPI = {
  // Search items by name (autocomplete)
  search: async (query, limit = 20) => {
    const response = await client.get('/items/search', {
      params: { q: query, limit }
    });
    return response.data;
  },

  // Get item by ID with price information
  getById: async (id) => {
    const response = await client.get(`/items/${id}`);
    return response.data;
  },

  // List all items with optional filtering
  getAll: async (skip = 0, limit = 100, itemType = null) => {
    const params = { skip, limit };
    if (itemType) params.item_type = itemType;

    const response = await client.get('/items/', { params });
    return response.data;
  }
};