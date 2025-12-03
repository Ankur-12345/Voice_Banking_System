import React, { useState } from 'react';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import { voiceService } from '../../services/voiceService';

const VoiceCommand = ({ onCommandProcessed }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [voiceMessage, setVoiceMessage] = useState('');

  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();

  if (!browserSupportsSpeechRecognition) {
    return <div>Browser doesn't support speech recognition.</div>;
  }

  const startListening = () => {
    resetTranscript();
    setVoiceMessage('');
    SpeechRecognition.startListening({ continuous: false });
  };

  const stopListening = async () => {
    SpeechRecognition.stopListening();
    if (transcript) {
      setIsProcessing(false);
      try {
        const result = await voiceService.processCommand(transcript);
        setVoiceMessage(getResponseMessage(result));
        onCommandProcessed(result);
      } catch (err) {
        setVoiceMessage('Failed to process command');
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const getResponseMessage = (result) => {
    switch (result.action) {
      case 'check_balance':
        return `Your current balance is $${result.data.balance.toFixed(2)}`;
      case 'transfer':
        return `Transfer successful! New balance: $${result.data.new_balance.toFixed(2)}`;
      case 'transaction_history':
        return 'Displaying transaction history below';
      case 'unknown':
        return 'Sorry, I did not understand that command. Try saying "check balance" or "transfer 100 to ACC1234567890"';
      default:
        return 'Command processed';
    }
  };

  return (
    <div className="voice-command-section">
      <h2>🎤 Voice Commands</h2>
      <div className="voice-controls">
        <button 
          onClick={startListening} 
          disabled={listening || isProcessing}
          className="voice-btn start"
        >
          {listening ? 'Listening...' : 'Start Voice Command'}
        </button>
        <button 
          onClick={stopListening} 
          //disabled={!listening || isProcessing}
          className="voice-btn stop"
        >
          Process Command
        </button>
      </div>
      
      {transcript && (
        <div className="transcript">
          <strong>You said:</strong> {transcript}
        </div>
      )}
      
      {isProcessing && <p className="processing">Processing your command...</p>}
      
      {voiceMessage && (
        <div className="voice-response">
          <strong>Response:</strong> {voiceMessage}
        </div>
      )}

      <div className="voice-commands-help">
        <h3>Available Commands:</h3>
        <ul>
          <li>"Check balance" or "What is my balance"</li>
          <li>"Transfer [amount] to [account]" (e.g., "Transfer 50 to ACC1234567890")</li>
          <li>"Show transaction history"</li>
        </ul>
      </div>
    </div>
  );
};

export default VoiceCommand;
