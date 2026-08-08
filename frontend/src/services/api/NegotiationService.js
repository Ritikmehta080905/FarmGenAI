import { api } from './index';

export const NegotiationService = {
  /**
   * Fetch active negotiation state by ID.
   * @param {string} id - Negotiation ID
   * @returns {Promise<Object>} Negotiation state
   */
  getNegotiation: async (id) => {
    const response = await api.get(`/negotiations/${id}`);
    return response.data;
  },

  /**
   * Accept the current offer.
   * @param {string} id - Negotiation ID
   * @returns {Promise<Object>}
   */
  acceptOffer: async (id) => {
    const response = await api.post(`/negotiations/${id}/accept`);
    return response.data;
  },

  /**
   * Reject the current offer and abort.
   * @param {string} id - Negotiation ID
   * @returns {Promise<Object>}
   */
  rejectOffer: async (id) => {
    const response = await api.post(`/negotiations/${id}/reject`);
    return response.data;
  },

  /**
   * Intervene with a manual counteroffer.
   * @param {string} id - Negotiation ID
   * @param {number} price - Human counter price
   * @returns {Promise<Object>}
   */
  intervene: async (id, price) => {
    const response = await api.post(`/negotiations/${id}/intervene`, { override_price: price });
    return response.data;
  },

  /**
   * Submit Reinforcement Learning feedback after a deal.
   * @param {string} id - Negotiation ID
   * @param {Object} feedback - { rating: number, feedback: string }
   * @returns {Promise<Object>}
   */
  submitFeedback: async (id, feedback) => {
    const response = await api.post(`/negotiations/${id}/feedback`, feedback);
    return response.data;
  }
};
