import React, { useState } from 'react';
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

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear messages when user types
    setError('');
    setSuccess('');
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
      setSuccess(`✅ Transfer successful! New balance: $${result.new_balance.toFixed(2)}`);
      
      // Reset form
      setFormData({
        recipient_account: '',
        amount: '',
        description: ''
      });
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Transfer failed. Please try again.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const formatAccountNumber = (value) => {
    // Auto-format account number as user types
    return value.toUpperCase().replace(/[^A-Z0-9]/g, '');
  };

  return (
    <div className="fund-transfer-container">
      <div className="transfer-card">
        <h2>💸 Fund Transfer</h2>
        
        <form onSubmit={handleSubmit} className="transfer-form">
          <div className="form-group">
            <label htmlFor="recipient_account">Recipient Account Number *</label>
            <input
              type="text"
              id="recipient_account"
              name="recipient_account"
              value={formData.recipient_account}
              onChange={(e) => setFormData({
                ...formData,
                recipient_account: formatAccountNumber(e.target.value)
              })}
              placeholder="ACC1234567890"
              maxLength="13"
              required
              disabled={loading}
            />
            <small>Format: ACC followed by 10 digits</small>
          </div>

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
            disabled={loading}
          >
            {loading ? 'Processing...' : '➤ Transfer Funds'}
          </button>
        </form>

        <div className="transfer-tips">
          <h4>💡 Transfer Tips:</h4>
          <ul>
            <li>Double-check the recipient account number</li>
            <li>Ensure you have sufficient balance</li>
            <li>Transfers are processed instantly</li>
            <li>You'll receive a confirmation after successful transfer</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default FundTransfer;
