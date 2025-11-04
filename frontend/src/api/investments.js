import apiClient from "./client";

export const investmentAPI = {
    getAll: async (skip = 0, limit = 100) => {
        console.log('Getting all investments...');
        const response = await apiClient.get("/investments/",{
            params: {skip, limit}
        });
        console.log('Got investments:', response.data);
        return response.data;
    } ,

    getById: async (id) => {
        const response = await apiClient.post(`/investments/${id}`);
        return response.data;
    },

    create: async (data) => {
        console.log('Creating investment with data:', data);
        try {
            const response = await apiClient.post('/investments/', data);
            console.log('Investment created successfully:', response.data);
            return response.data;
        } catch (error) {
            console.error('Error creating investment:', error);
            console.error('Error response:', error.response);
            throw error;
        }
    },

    update: async (id, data) => {
        const response = await apiClient.patch(`/investments/${id}`, data);
        return response.data;
    },

    delete: async (id) => {
        await apiClient.delete(`/investments/${id}`)
    },

    refreshPrice: async (id) => {
        const response = await apiClient.post(`/prices/refresh/${id}`);
        return response.data;
    },

    refreshAllPrices: async () => {
        const response = await apiClient.post('/prices/refresh-all');
        return response.data;
    },

    getPriceHistory: async (id, days = null) => {
        const params = days ? { days } : {};
        const response = await apiClient.get(`/price_history/${id}`, { params });
        return response.data;
    },

    getPortfolioValueHistory: async (days = 30) => {
        const response = await apiClient.get('/portfolio/value-history', {
            params: { days }
        });
        return response.data;
    },

    getTopPerformers: async (limit = 3) => {
        const response = await apiClient.get('/portfolio/top-performers', {
            params: { limit }
        });
        return response.data;
    },
};