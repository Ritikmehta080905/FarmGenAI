import { api } from '@/services/api';

export const negotiationService = {
  getNegotiation: async (id) => {
    const response = await api.get(`/negotiations/${id}`);
    return response.data;
  },

  acceptOffer: async (id) => {
    const response = await api.post(`/negotiations/${id}/accept`);
    return response.data;
  },

  rejectOffer: async (id) => {
    const response = await api.post(`/negotiations/${id}/reject`);
    return response.data;
  },

  intervene: async (id, price) => {
    const response = await api.post(`/negotiations/${id}/intervene`, { override_price: price });
    return response.data;
  },

  submitFeedback: async (id, feedback) => {
    const response = await api.post(`/negotiations/${id}/feedback`, feedback);
    return response.data;
  }
};

export default negotiationService;
