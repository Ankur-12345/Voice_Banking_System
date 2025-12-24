import React, { useState, useEffect, useCallback } from 'react';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import { voiceService } from '../../services/voiceService';
import './VoiceCommand.css';

const VoiceCommand = ({ onCommandProcessed }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [voiceMessage, setVoiceMessage] = useState('');
  const [error, setError] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [selectedVoice, setSelectedVoice] = useState(null);
  const [availableVoices, setAvailableVoices] = useState([]);
  
  // OTP States
  const [otpRequired, setOtpRequired] = useState(false);
  const [transactionId, setTransactionId] = useState('');
  const [otpValue, setOtpValue] = useState('');
  const [pendingTransferInfo, setPendingTransferInfo] = useState(null);
  const [otpError, setOtpError] = useState('');

  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();

  // Load available voices
  useEffect(() => {
    const loadVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      setAvailableVoices(voices);
      
      // Try to select a female English voice by default
      const femaleVoice = voices.find(voice => 
        voice.lang.startsWith('en') && 
        (voice.name.toLowerCase().includes('female') || 
         voice.name.toLowerCase().includes('woman') ||
         voice.name.includes('Samantha') ||
         voice.name.includes('Victoria') ||
         voice.name.includes('Karen') ||
         voice.name.includes('Zira'))
      ) || voices.find(voice => voice.lang.startsWith('en'));
      
      setSelectedVoice(femaleVoice);
    };

    loadVoices();
    
    // Chrome loads voices asynchronously
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  // Text-to-Speech function
  const speak = useCallback((text) => {
    if (!voiceEnabled) return;
    
    // Cancel any ongoing speech
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Configure the voice
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }
    
    utterance.rate = 1.0;
    utterance.pitch = 1.1;
    utterance.volume = 1.0;
    
    utterance.onstart = () => {
      setIsSpeaking(true);
    };
    
    utterance.onend = () => {
      setIsSpeaking(false);
    };
    
    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      setIsSpeaking(false);
    };
    
    window.speechSynthesis.speak(utterance);
  }, [voiceEnabled, selectedVoice]);

  // Stop speaking
  const stopSpeaking = useCallback(() => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, []);

  // Auto-process when listening stops and we have a transcript
  useEffect(() => {
    const processTranscript = async () => {
      if (!listening && transcript && transcript.trim() && !isProcessing && isListening) {
        setIsListening(false);
        setIsProcessing(true);
        setError('');
        
        // Acknowledge that we heard the command
        speak("Processing your command");
        
        try {
          console.log('Auto-processing transcript:', transcript);
          const result = await voiceService.processCommand(transcript);
          console.log('Received result:', result);
          
          // Check if OTP is required
          if (result.requires_otp) {
            setOtpRequired(true);
            setTransactionId(result.transaction_id);
            setPendingTransferInfo(result.data);
            setVoiceMessage(result.message);
            speak(result.message);
          } else {
            const responseMsg = getResponseMessage(result);
            setVoiceMessage(responseMsg);
            speak(responseMsg);
            
            // Call the parent callback
            if (onCommandProcessed) {
              onCommandProcessed(result);
            }
          }
          
          resetTranscript();
        } catch (err) {
          console.error('Voice processing error:', err);
          const errorMsg = err.response?.data?.detail || err.message || 'Failed to process command';
          setError(errorMsg);
          setVoiceMessage('');
          speak(`Sorry, ${errorMsg}`);
        } finally {
          setIsProcessing(false);
        }
      }
    };

    processTranscript();
  }, [listening, transcript, isProcessing, isListening, onCommandProcessed, resetTranscript, speak]);

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
    
    // Announce that we're ready to listen
    speak("I'm ready, please speak your command");
    
    // Wait a bit for the speech to finish before starting listening
    setTimeout(() => {
      SpeechRecognition.startListening({ 
        continuous: false,
        language: 'en-US'
      });
    }, 1500);
  };

  const stopListening = () => {
    SpeechRecognition.stopListening();
    setIsListening(false);
    stopSpeaking();
  };

  const toggleVoice = () => {
    setVoiceEnabled(!voiceEnabled);
    if (!voiceEnabled) {
      speak("Voice responses enabled");
    }
  };

  const handleVoiceChange = (e) => {
    const voice = availableVoices.find(v => v.name === e.target.value);
    setSelectedVoice(voice);
    if (voice) {
      const utterance = new SpeechSynthesisUtterance("Hello, this is how I sound");
      utterance.voice = voice;
      utterance.pitch = 1.1;
      window.speechSynthesis.speak(utterance);
    }
  };

  const handleOTPSubmit = async (e) => {
    e.preventDefault();
    setOtpError('');
    
    if (otpValue.length !== 6) {
      setOtpError('OTP must be 6 digits');
      return;
    }
    
    try {
      setIsProcessing(true);
      const response = await voiceService.verifyOTP(transactionId, otpValue);
      
      setVoiceMessage(response.message);
      speak(response.message);
      
      // Reset OTP state
      setOtpRequired(false);
      setOtpValue('');
      setTransactionId('');
      setPendingTransferInfo(null);
      setOtpError('');
      
      // Refresh balance and transactions
      if (onCommandProcessed) {
        onCommandProcessed(response);
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'OTP verification failed';
      setOtpError(errorMsg);
      speak(errorMsg);
    } finally {
      setIsProcessing(false);
    }
  };

  const cancelOTP = () => {
    setOtpRequired(false);
    setOtpValue('');
    setTransactionId('');
    setPendingTransferInfo(null);
    setOtpError('');
    speak("Transaction cancelled");
  };

  const getResponseMessage = (result) => {
    switch (result.action) {
      case 'check_balance':
        return `Your current account balance is ${result.data?.balance?.toFixed(2)} dollars`;
      case 'transfer':
        return result.message || `Transfer successful! Your new balance is ${result.data?.sender?.new_balance?.toFixed(2)} dollars`;
      case 'transfer_pending':
        return result.message;
      case 'transaction_history':
        const count = result.data?.transactions?.length || 0;
        return `I found ${count} recent transactions for you`;
      case 'help':
        return 'I can help you with checking your bank account balance, transferring money, and viewing transaction history. Just ask me what you need.';
      case 'rejected':
        return result.message || 'Sorry, I can only help with banking services like checking your account balance, transferring money, or viewing transactions.';
      case 'clarify':
        return result.message || 'I did not understand that. Could you please rephrase your request?';
      case 'error':
        return result.message || 'An error occurred while processing your command.';
      case 'unknown':
        return result.message || 'Sorry, I did not understand that command. Please try again.';
      default:
        return 'Command processed successfully';
    }
  };

  return (
    <div className="voice-command-section">
      <h2>🎤 Voice Banking Assistant</h2>
      <p className="subtitle">Speak naturally - I'll respond and process your command automatically</p>
      
      {/* Voice Settings */}
      <div className="voice-settings">
        <div className="setting-item">
          <label className="toggle-switch">
            <input 
              type="checkbox" 
              checked={voiceEnabled} 
              onChange={toggleVoice}
            />
            <span className="slider"></span>
          </label>
          <span className="setting-label">
            {voiceEnabled ? '🔊 Voice Responses On' : '🔇 Voice Responses Off'}
          </span>
        </div>
        
        {availableVoices.length > 0 && (
          <div className="setting-item voice-selector">
            <label>Voice:</label>
            <select 
              value={selectedVoice?.name || ''} 
              onChange={handleVoiceChange}
              disabled={!voiceEnabled}
            >
              {availableVoices
                .filter(voice => voice.lang.startsWith('en'))
                .map((voice, index) => (
                  <option key={index} value={voice.name}>
                    {voice.name} ({voice.lang})
                  </option>
                ))
              }
            </select>
          </div>
        )}
      </div>
      
      {/* OTP Verification Box */}
      {otpRequired && (
        <div className="otp-verification-box">
          <div className="otp-header">
            <h3>🔐 Security Verification Required</h3>
          </div>
          <div className="otp-content">
            <div className="transaction-info">
              <p><strong>Transfer Amount:</strong> ${pendingTransferInfo?.amount?.toFixed(2)}</p>
              <p><strong>Recipient:</strong> {pendingTransferInfo?.recipient}</p>
            </div>
            <p className="otp-instruction">
              An OTP has been sent to your registered email. Please enter it below to complete the transaction.
            </p>
            <form onSubmit={handleOTPSubmit} className="otp-form">
              <div className="otp-input-group">
                <input
                  type="text"
                  value={otpValue}
                  onChange={(e) => setOtpValue(e.target.value.replace(/\D/g, ''))}
                  placeholder="Enter 6-digit OTP"
                  maxLength="6"
                  className="otp-input"
                  required
                  autoFocus
                  disabled={isProcessing}
                />
              </div>
              {otpError && <div className="otp-error">{otpError}</div>}
              <div className="otp-buttons">
                <button type="submit" className="verify-btn" disabled={isProcessing}>
                  {isProcessing ? 'Verifying...' : '✓ Verify & Transfer'}
                </button>
                <button type="button" className="cancel-btn" onClick={cancelOTP} disabled={isProcessing}>
                  ✕ Cancel
                </button>
              </div>
            </form>
            <p className="otp-note">⏱️ OTP expires in 5 minutes. Max 3 attempts allowed.</p>
          </div>
        </div>
      )}
      
      <div className="voice-controls">
        <button 
          onClick={listening ? stopListening : startListening}
          disabled={isProcessing || otpRequired}
          className={`voice-btn ${listening ? 'listening' : isSpeaking ? 'speaking' : 'idle'}`}
        >
          {isSpeaking ? (
            <>
              <span className="speaker-icon">🔊</span>
              <span>Speaking...</span>
            </>
          ) : listening ? (
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
      
      {isSpeaking && (
        <div className="speaking-indicator">
          <div className="speaker-animation">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <p>Assistant is speaking...</p>
        </div>
      )}
      
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
      
      {isProcessing && !isSpeaking && !otpRequired && (
        <div className="processing-box">
          <div className="spinner"></div>
          <p>🔄 Processing your command...</p>
        </div>
      )}
      
      {voiceMessage && !otpRequired && (
        <div className="voice-response success">
          <div className="response-icon">✅</div>
          <div className="response-content">
            <strong>Assistant Response:</strong>
            <p>{voiceMessage}</p>
          </div>
        </div>
      )}

      {error && !otpRequired && (
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
            <h4>Transfer Funds (OTP Protected)</h4>
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
        
        <div className="security-notice">
          <h4>🔐 Security Notice</h4>
          <p>Voice transfers require OTP verification sent to your registered email for your protection.</p>
        </div>
        
        <div className="tip-box">
          <strong>💡 Pro Tip:</strong> I'll talk back to you! Enable voice responses above, 
          click the microphone, speak clearly, and I'll confirm what I heard and respond with a voice.
          For transfers, you'll receive an OTP via email for verification.
        </div>
      </div>
    </div>
  );
};

export default VoiceCommand;
