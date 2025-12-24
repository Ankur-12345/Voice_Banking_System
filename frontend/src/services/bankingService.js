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

  verifyTransferOTP: async (transactionId, otp) => {
    const response = await api.post('/api/banking/verify-transfer', {
      transaction_id: transactionId,
      otp: otp
    });
    return response.data;
  },

  getTransactions: async () => {
    const response = await api.get('/api/banking/transactions');
    return response.data;
  },

  getRecentRecipients: async () => {
    const response = await api.get('/api/banking/recent-recipients');
    return response.data;
  },

  searchAccounts: async (query) => {
    const response = await api.get(`/api/banking/search-accounts/${encodeURIComponent(query)}`);
    return response.data;
  },

  validateAccount: async (accountNumber) => {
    const response = await api.get(`/api/banking/validate-account/${accountNumber}`);
    return response.data;
  },

  getAllUsers: async () => {
    const response = await api.get('/api/banking/all-users');
    return response.data;
  }
};
