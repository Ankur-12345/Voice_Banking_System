import api from './api';

export const bankingService = {
  getBalance: async () => {
    const response = await api.get('/api/banking/balance');
    return response.data;
  },

  transferFunds: async (transferData) => {
    const response = await api.post('/api/banking/transfer', transferData);
    return response.data;
  },

  getTransactions: async () => {
    const response = await api.get('/api/banking/transactions');
    return response.data;
  }
};
