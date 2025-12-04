import React, { useState, useEffect } from 'react';
import { bankingService } from '../../services/bankingService';
import './FundTransfer.css';

const FundTransfer = () => {
  const [formData, setFormData] = useState({
    recipient_account: '',
    amount: '',
    description: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [recentRecipients, setRecentRecipients] = useState([]);
  const [showSearch, setShowSearch] = useState(false);
  const [recipientInfo, setRecipientInfo] = useState(null);
  const [validatingAccount, setValidatingAccount] = useState(false);

  useEffect(() => {
    fetchRecentRecipients();
  }, []);

  const fetchRecentRecipients = async () => {
    try {
      const response = await bankingService.getRecentRecipients();
      setRecentRecipients(response);
    } catch (err) {
      console.error('Failed to fetch recent recipients:', err);
    }
  };

  const searchAccounts = async (query) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      const response = await bankingService.searchAccounts(query);
      setSearchResults(response.results);
    } catch (err) {
      console.error('Search error:', err);
    }
  };

  const handleSearchChange = (e) => {
    const value = e.target.value;
    setSearchQuery(value);
    searchAccounts(value);
  };

  const validateAccount = async (accountNumber) => {
    if (accountNumber.length !== 13) return;

    setValidatingAccount(true);
    try {
      const response = await bankingService.validateAccount(accountNumber);
      if (response.valid) {
        setRecipientInfo({
          account_number: response.account_number,
          username: response.username,
          full_name: response.full_name
        });
        setError('');
      } else {
        setRecipientInfo(null);
        setError(response.message);
      }
    } catch (err) {
      setRecipientInfo(null);
      setError('Failed to validate account');
    } finally {
      setValidatingAccount(false);
    }
  };

  const selectRecipient = (recipient) => {
    setFormData({
      ...formData,
      recipient_account: recipient.account_number
    });
    setRecipientInfo(recipient);
    setShowSearch(false);
    setSearchQuery('');
    setSearchResults([]);
    setError('');
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    if (name === 'recipient_account') {
      const formatted = formatAccountNumber(value);
      setFormData(prev => ({
        ...prev,
        [name]: formatted
      }));
      
      // Validate account when length is 13
      if (formatted.length === 13) {
        validateAccount(formatted);
      } else {
        setRecipientInfo(null);
      }
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
    
    setError('');
    setSuccess('');
  };

  const formatAccountNumber = (value) => {
    return value.toUpperCase().replace(/[^A-Z0-9]/g, '').substring(0, 13);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    // Validation
    if (!formData.recipient_account || !formData.amount) {
      setError('Please fill in all required fields');
      setLoading(false);
      return;
    }

    if (!recipientInfo) {
      setError('Please enter a valid recipient account');
      setLoading(false);
      return;
    }

    if (parseFloat(formData.amount) <= 0) {
      setError('Amount must be greater than zero');
      setLoading(false);
      return;
    }

    try {
      const transferData = {
        recipient_account: formData.recipient_account,
        amount: parseFloat(formData.amount),
        description: formData.description || 'Fund Transfer'
      };

      const result = await bankingService.transferFunds(transferData);
      setSuccess(`✅ ${result.message || 'Transfer successful!'} New balance: $${result.sender?.new_balance?.toFixed(2) || result.new_balance?.toFixed(2)}`);
      
      // Reset form
      setFormData({
        recipient_account: '',
        amount: '',
        description: ''
      });
      setRecipientInfo(null);
      
      // Refresh recent recipients
      fetchRecentRecipients();
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Transfer failed. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fund-transfer-container">
      <div className="transfer-card">
        <h2>💸 Fund Transfer</h2>

        {/* Recent Recipients */}
        {recentRecipients.length > 0 && (
          <div className="recent-recipients">
            <h4>Recent Recipients</h4>
            <div className="recipients-list">
              {recentRecipients.map((recipient, index) => (
                <div 
                  key={index} 
                  className="recipient-item"
                  onClick={() => selectRecipient(recipient)}
                >
                  <div className="recipient-avatar">
                    {recipient.username.charAt(0).toUpperCase()}
                  </div>
                  <div className="recipient-details">
                    <strong>{recipient.username}</strong>
                    <small>{recipient.account_number}</small>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="transfer-form">
          {/* Search Recipients */}
          <div className="form-group">
            <label>Search Recipients</label>
            <div className="search-container">
              <input
                type="text"
                placeholder="Search by username or account number..."
                value={searchQuery}
                onChange={handleSearchChange}
                onFocus={() => setShowSearch(true)}
              />
              <span className="search-icon">🔍</span>
            </div>

            {showSearch && searchResults.length > 0 && (
              <div className="search-results">
                {searchResults.map((result, index) => (
                  <div 
                    key={index} 
                    className="search-result-item"
                    onClick={() => selectRecipient(result)}
                  >
                    <div className="result-avatar">
                      {result.username.charAt(0).toUpperCase()}
                    </div>
                    <div className="result-info">
                      <strong>{result.username}</strong>
                      {result.full_name && <span className="full-name">{result.full_name}</span>}
                      <small>{result.account_number}</small>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recipient Account Number */}
          <div className="form-group">
            <label htmlFor="recipient_account">Recipient Account Number *</label>
            <input
              type="text"
              id="recipient_account"
              name="recipient_account"
              value={formData.recipient_account}
              onChange={handleChange}
              placeholder="ACC1234567890"
              maxLength="13"
              required
              disabled={loading}
            />
            <small>Format: ACC followed by 10 digits</small>
            
            {validatingAccount && (
              <div className="validating">
                <span className="spinner"></span> Validating account...
              </div>
            )}

            {recipientInfo && (
              <div className="recipient-confirmed">
                ✅ Recipient: <strong>{recipientInfo.username}</strong>
                {recipientInfo.full_name && ` (${recipientInfo.full_name})`}
              </div>
            )}
          </div>

          {/* Amount */}
          <div className="form-group">
            <label htmlFor="amount">Amount (USD) *</label>
            <input
              type="number"
              id="amount"
              name="amount"
              value={formData.amount}
              onChange={handleChange}
              placeholder="0.00"
              step="0.01"
              min="0.01"
              required
              disabled={loading}
            />
          </div>

          {/* Description */}
          <div className="form-group">
            <label htmlFor="description">Description (Optional)</label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Add a note for this transfer..."
              rows="3"
              disabled={loading}
            />
          </div>

          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          <button 
            type="submit" 
            className="submit-btn"
            disabled={loading || !recipientInfo}
          >
            {loading ? 'Processing...' : '➤ Transfer Funds'}
          </button>
        </form>

        <div className="transfer-tips">
          <h4>💡 Transfer Tips:</h4>
          <ul>
            <li>Search for recipients by username or account number</li>
            <li>Select from recent recipients for quick transfers</li>
            <li>Account number will be validated automatically</li>
            <li>Ensure you have sufficient balance</li>
            <li>Transfers are processed instantly</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default FundTransfer;
