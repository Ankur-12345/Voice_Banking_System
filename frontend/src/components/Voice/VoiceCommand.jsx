import React, { useState, useEffect } from 'react';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import { voiceService } from '../../services/voiceService';
import './VoiceCommand.css';

const VoiceCommand = ({ onCommandProcessed }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [voiceMessage, setVoiceMessage] = useState('');
  const [error, setError] = useState('');
  const [isListening, setIsListening] = useState(false);

  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();

  // Auto-process when listening stops and we have a transcript
  useEffect(() => {
    const processTranscript = async () => {
      // Only process if we were listening, stopped listening, have a transcript, and not already processing
      if (!listening && transcript && transcript.trim() && !isProcessing && isListening) {
        setIsListening(false);
        setIsProcessing(true);
        setError('');
        
        try {
          console.log('Auto-processing transcript:', transcript);
          const result = await voiceService.processCommand(transcript);
          console.log('Received result:', result);
          
          setVoiceMessage(getResponseMessage(result));
          
          // Call the parent callback
          if (onCommandProcessed) {
            onCommandProcessed(result);
          }
          
          // Clear transcript after processing
          resetTranscript();
        } catch (err) {
          console.error('Voice processing error:', err);
          const errorMsg = err.response?.data?.detail || err.message || 'Failed to process command';
          setError(errorMsg);
          setVoiceMessage('');
        } finally {
          setIsProcessing(false);
        }
      }
    };

    processTranscript();
  }, [listening, transcript, isProcessing, isListening, onCommandProcessed, resetTranscript]);

  if (!browserSupportsSpeechRecognition) {
    return (
      <div className="voice-command-section">
        <div className="error-box">
          <h3>❌ Browser Not Supported</h3>
          <p>Your browser doesn't support speech recognition.</p>
          <p>Please use Chrome, Edge, or Safari.</p>
        </div>
      </div>
    );
  }

  const startListening = () => {
    resetTranscript();
    setVoiceMessage('');
    setError('');
    setIsListening(true);
    // continuous: false means it will stop automatically when you stop speaking
    SpeechRecognition.startListening({ 
      continuous: false,
      language: 'en-US'
    });
  };

  const stopListening = () => {
    SpeechRecognition.stopListening();
    setIsListening(false);
  };

  const getResponseMessage = (result) => {
    switch (result.action) {
      case 'check_balance':
        return `Your current balance is $${result.data?.balance?.toFixed(2) || 'N/A'}`;
      case 'transfer':
        return result.message || `Transfer successful! New balance: $${result.data?.sender?.new_balance?.toFixed(2) || 'N/A'}`;
      case 'transaction_history':
        const count = result.data?.transactions?.length || 0;
        return `Showing ${count} recent transactions`;
      case 'help':
        return 'Voice commands are available. Check the list below.';
      case 'unknown':
        return result.message || 'Sorry, I did not understand that command.';
      default:
        return 'Command processed';
    }
  };

  return (
    <div className="voice-command-section">
      <h2>🎤 Voice Commands</h2>
      <p className="subtitle">Speak naturally - your command will be processed automatically when you finish speaking</p>
      
      <div className="voice-controls">
        <button 
          onClick={listening ? stopListening : startListening}
          disabled={isProcessing}
          className={`voice-btn ${listening ? 'listening' : 'idle'}`}
        >
          {listening ? (
            <>
              <span className="pulse-icon">🔴</span>
              <span>Listening... Speak now!</span>
            </>
          ) : isProcessing ? (
            <>
              <span className="spinner-icon">⏳</span>
              <span>Processing...</span>
            </>
          ) : (
            <>
              <span>🎤</span>
              <span>Click to Speak</span>
            </>
          )}
        </button>
      </div>
      
      {listening && (
        <div className="listening-indicator">
          <div className="sound-wave">
            <span></span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
          </div>
          <p>I'm listening... Speak your command</p>
        </div>
      )}
      
      {transcript && (
        <div className="transcript-box">
          <strong>You said:</strong> 
          <span className="transcript-text">"{transcript}"</span>
        </div>
      )}
      
      {isProcessing && (
        <div className="processing-box">
          <div className="spinner"></div>
          <p>🔄 Processing your command...</p>
        </div>
      )}
      
      {voiceMessage && (
        <div className="voice-response success">
          <div className="response-icon">✅</div>
          <div className="response-content">
            <strong>Response:</strong>
            <p>{voiceMessage}</p>
          </div>
        </div>
      )}

      {error && (
        <div className="voice-response error">
          <div className="response-icon">❌</div>
          <div className="response-content">
            <strong>Error:</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      <div className="voice-commands-help">
        <h3>💡 Available Voice Commands:</h3>
        <div className="commands-grid">
          <div className="command-card">
            <div className="command-icon">💰</div>
            <h4>Check Balance</h4>
            <ul>
              <li>"Check balance"</li>
              <li>"What is my balance"</li>
              <li>"Show my balance"</li>
            </ul>
          </div>
          
          <div className="command-card">
            <div className="command-icon">💸</div>
            <h4>Transfer Funds</h4>
            <ul>
              <li>"Transfer 100 to ACC1234567890"</li>
              <li>"Send 50 to user bob"</li>
              <li>"Pay 25 dollars to alice"</li>
            </ul>
          </div>
          
          <div className="command-card">
            <div className="command-icon">📝</div>
            <h4>Transaction History</h4>
            <ul>
              <li>"Show transaction history"</li>
              <li>"Last 5 transactions"</li>
              <li>"Show my transactions"</li>
            </ul>
          </div>
          
          <div className="command-card">
            <div className="command-icon">❓</div>
            <h4>Help</h4>
            <ul>
              <li>"Help"</li>
              <li>"What can you do"</li>
              <li>"Show commands"</li>
            </ul>
          </div>
        </div>
        
        <div className="tip-box">
          <strong>💡 Pro Tip:</strong> Just click the button, speak clearly, and stop. 
          Your command will be processed automatically when you finish speaking!
        </div>
      </div>
    </div>
  );
};


export default VoiceCommand;
