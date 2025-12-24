import React, { useState, useEffect } from 'react';
import { bankingService } from '../../services/bankingService';
import './FundTransfer.css';

const FundTransfer = () => {
  const [formData, setFormData] = useState({
    recipient_account: '',
    amount: '',
    description: ''
  });
  const [recentRecipients, setRecentRecipients] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [validating, setValidating] = useState(false);
  const [validAccount, setValidAccount] = useState(null);
  
  // OTP States
  const [otpRequired, setOtpRequired] = useState(false);
  const [transactionId, setTransactionId] = useState('');
  const [otpValue, setOtpValue] = useState('');
  const [pendingTransferInfo, setPendingTransferInfo] = useState(null);
  const [otpError, setOtpError] = useState('');

  useEffect(() => {
    fetchRecentRecipients();
  }, []);

  const fetchRecentRecipients = async () => {
    try {
      const data = await bankingService.getRecentRecipients();
      setRecentRecipients(data.recipients || []);
    } catch (err) {
      console.error('Failed to fetch recent recipients:', err);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
    setMessage('');
    setError('');

    if (name === 'recipient_account') {
      if (value.length === 13) {
        validateAccount(value);
      } else {
        setValidAccount(null);
      }
    }
  };

  const validateAccount = async (accountNumber) => {
    console.log('Validating account:', accountNumber);
    setValidating(true);
    setValidAccount(null);
    
    try {
      const result = await bankingService.validateAccount(accountNumber);
      console.log('Validation result:', result);
      setValidAccount(result);
    } catch (err) {
      console.error('Validation error:', err);
      setValidAccount({ valid: false, message: 'Account not found' });
    } finally {
      setValidating(false);
    }
  };

  const handleSearch = async (query) => {
    setSearchQuery(query);
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      const data = await bankingService.searchAccounts(query);
      setSearchResults(data.results || []);
    } catch (err) {
      console.error('Search failed:', err);
      setSearchResults([]);
    }
  };

  const selectRecipient = (account) => {
    setFormData({
      ...formData,
      recipient_account: account.account_number,
      description: `Transfer to ${account.username}`
    });
    setSearchQuery('');
    setSearchResults([]);
    setValidAccount({
      valid: true,
      username: account.username,
      full_name: account.full_name,
      account_number: account.account_number
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Final validation check
    if (!validAccount || !validAccount.valid) {
      setError('Please enter a valid recipient account');
      return;
    }
    
    setLoading(true);
    setMessage('');
    setError('');

    try {
      const response = await bankingService.transferFunds(formData);
      
      if (response.requires_otp) {
        // OTP is required
        setOtpRequired(true);
        setTransactionId(response.transaction_id);
        setPendingTransferInfo(response.data);
        setMessage(response.message);
      } else {
        // Transfer completed
        setMessage(response.message || 'Transfer successful!');
        setFormData({ recipient_account: '', amount: '', description: '' });
        setValidAccount(null);
        fetchRecentRecipients();
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Transfer failed. Please try again.');
    } finally {
      setLoading(false);
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
      setLoading(true);
      const response = await bankingService.verifyTransferOTP(transactionId, otpValue);
      
      setMessage(response.message);
      
      // Reset everything
      setOtpRequired(false);
      setOtpValue('');
      setTransactionId('');
      setPendingTransferInfo(null);
      setOtpError('');
      setFormData({ recipient_account: '', amount: '', description: '' });
      setValidAccount(null);
      
      fetchRecentRecipients();
      
      setTimeout(() => setMessage(''), 5000);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'OTP verification failed';
      setOtpError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const cancelOTP = () => {
    setOtpRequired(false);
    setOtpValue('');
    setTransactionId('');
    setPendingTransferInfo(null);
    setOtpError('');
    setMessage('');
  };

  return (
    <div className="fund-transfer-container">
      <div className="fund-transfer-card">
        <h2>💸 Fund Transfer</h2>
        <p className="subtitle">Transfer funds securely with OTP verification</p>

        {message && !otpRequired && <div className="success-message">{message}</div>}
        {error && <div className="error-message">{error}</div>}

        {/* OTP Verification Modal */}
        {otpRequired && (
          <div className="otp-modal-overlay">
            <div className="otp-modal-box">
              <div className="otp-modal-header">
                <h3>🔐 Verify Your Transfer</h3>
              </div>
              <div className="otp-modal-body">
                <div className="transfer-summary-box">
                  <p><strong>Amount:</strong> ${pendingTransferInfo?.amount?.toFixed(2)}</p>
                  <p><strong>Recipient:</strong> {pendingTransferInfo?.recipient}</p>
                  <p><strong>Account:</strong> {pendingTransferInfo?.recipient_account}</p>
                </div>
                <p className="otp-instruction-text">
                  An OTP has been sent to your registered email. Enter it below to complete the transfer.
                </p>
                <form onSubmit={handleOTPSubmit} className="otp-verification-form">
                  <input
                    type="text"
                    value={otpValue}
                    onChange={(e) => setOtpValue(e.target.value.replace(/\D/g, ''))}
                    placeholder="Enter 6-digit OTP"
                    maxLength="6"
                    className="otp-code-input"
                    required
                    autoFocus
                    disabled={loading}
                  />
                  {otpError && <div className="otp-error-msg">{otpError}</div>}
                  <div className="otp-action-buttons">
                    <button type="submit" className="otp-verify-button" disabled={loading}>
                      {loading ? 'Verifying...' : '✓ Verify & Transfer'}
                    </button>
                    <button type="button" className="otp-cancel-button" onClick={cancelOTP} disabled={loading}>
                      ✕ Cancel
                    </button>
                  </div>
                </form>
                <p className="otp-expiry-note">⏱️ OTP expires in 5 minutes</p>
              </div>
            </div>
          </div>
        )}

        {!otpRequired && (
          <>
            {/* Search Bar */}
            <div className="search-section">
              <h3>🔍 Search Recipients</h3>
              <input
                type="text"
                placeholder="Search by username or account number..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="search-input"
              />
              {searchResults.length > 0 && (
                <div className="search-results">
                  {searchResults.map((result, index) => (
                    <div
                      key={index}
                      className="search-result-item"
                      onClick={() => selectRecipient(result)}
                    >
                      <div className="result-info">
                        <strong>{result.username}</strong>
                        {result.full_name && <span className="full-name">{result.full_name}</span>}
                        <code className="account-num">{result.account_number}</code>
                      </div>
                      <button type="button" className="select-btn">Select</button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recent Recipients */}
            {recentRecipients.length > 0 && (
              <div className="recent-recipients">
                <h3>📋 Recent Recipients</h3>
                <div className="recipients-list">
                  {recentRecipients.map((recipient, index) => (
                    <div
                      key={index}
                      className="recipient-chip"
                      onClick={() => selectRecipient(recipient)}
                    >
                      <span className="recipient-icon">👤</span>
                      <span className="recipient-name">{recipient.username}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Transfer Form */}
            <form onSubmit={handleSubmit} className="transfer-form">
              <div className="form-group">
                <label>Recipient Account Number *</label>
                <div className="input-with-validation">
                  <input
                    type="text"
                    name="recipient_account"
                    placeholder="ACC1234567890"
                    value={formData.recipient_account}
                    onChange={handleChange}
                    required
                    maxLength="13"
                    className={validAccount?.valid ? 'input-valid' : validAccount?.valid === false ? 'input-invalid' : ''}
                  />
                  {validating && <span className="validating-text">Checking...</span>}
                  {validAccount?.valid && (
                    <div className="validation-success">
                      ✓ {validAccount.username}
                      {validAccount.full_name && ` (${validAccount.full_name})`}
                    </div>
                  )}
                  {validAccount?.valid === false && (
                    <div className="validation-error">✗ Account not found</div>
                  )}
                </div>
              </div>

              <div className="form-group">
                <label>Amount ($) *</label>
                <input
                  type="number"
                  name="amount"
                  placeholder="0.00"
                  value={formData.amount}
                  onChange={handleChange}
                  step="0.01"
                  min="0.01"
                  required
                />
              </div>

              <div className="form-group">
                <label>Description (Optional)</label>
                <input
                  type="text"
                  name="description"
                  placeholder="Add a note..."
                  value={formData.description}
                  onChange={handleChange}
                  maxLength="200"
                />
              </div>

              <button
                type="submit"
                className="transfer-btn"
                disabled={loading || !validAccount?.valid}
              >
                {loading ? 'Processing...' : '💸 Initiate Transfer'}
              </button>
            </form>

            <div className="security-info-box">
              <p>🔐 All transfers require OTP verification sent to your email</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default FundTransfer;
