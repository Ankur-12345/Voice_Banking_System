import api from './api';

export const voiceService = {
  /**
   * Process a voice command transcript
   * @param {string} transcript - The voice command text
   * @returns {Promise} - Response with action, data, and message
   */
  processCommand: async (transcript) => {
    const response = await api.post('/api/voice/process', {
      transcript: transcript
    });
    return response.data;
  },

  /**
   * Verify OTP for pending transaction
   * @param {string} transactionId - Transaction ID
   * @param {string} otp - 6-digit OTP code
   * @returns {Promise} - Transfer result
   */
  verifyOTP: async (transactionId, otp) => {
    const response = await api.post('/api/voice/verify-otp', {
      transaction_id: transactionId,
      otp: otp
    });
    return response.data;
  },

  /**
   * Get available voice commands
   * @returns {Promise} - List of available commands
   */
  getAvailableCommands: async () => {
    const response = await api.get('/api/voice/commands');
    return response.data;
  },

  /**
   * Test voice service connection
   * @returns {Promise} - Connection status
   */
  testConnection: async () => {
    try {
      const response = await api.get('/api/voice/commands');
      return {
        connected: true,
        message: 'Voice service is available',
        data: response.data
      };
    } catch (error) {
      return {
        connected: false,
        message: error.message || 'Voice service unavailable',
        error: error
      };
    }
  }
};
