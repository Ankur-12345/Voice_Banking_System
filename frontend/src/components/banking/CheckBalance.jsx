import React, { useState, useEffect } from 'react';
import { bankingService } from '../../services/bankingService';
import './CheckBalance.css';

const CheckBalance = () => {
  const [balance, setBalance] = useState(null);
  const [accountNumber, setAccountNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchBalance();
  }, []);

  const fetchBalance = async () => {
    setLoading(true);
    setError('');
    
    try {
      const data = await bankingService.getBalance();
      setBalance(data.balance);
      setAccountNumber(data.account_number);
    } catch (err) {
      setError('Failed to fetch balance. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  return (
    <div className="check-balance-container">
      <div className="balance-card">
        <h2>💰 Account Balance</h2>
        
        {loading && <div className="loading-spinner">Loading...</div>}
        
        {error && <div className="error-message">{error}</div>}
        
        {!loading && !error && balance !== null && (
          <div className="balance-info">
            <div className="balance-amount">
              <p className="label">Current Balance</p>
              <h1 className="amount">{formatCurrency(balance)}</h1>
            </div>
            
            <div className="account-info">
              <p className="label">Account Number</p>
              <p className="account-number">{accountNumber}</p>
            </div>
            
            <button onClick={fetchBalance} className="refresh-btn">
              🔄 Refresh Balance
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CheckBalance;
