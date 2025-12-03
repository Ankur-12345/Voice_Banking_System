import api from './api';

export const voiceService = {
  processCommand: async (transcript) => {
    const response = await api.post('/api/voice/process', { transcript });
    return response.data;
  }
};
