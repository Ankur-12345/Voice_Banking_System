import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../../services/authService';
import { bankingService } from '../../services/bankingService';
import VoiceCommand from '../Voice/VoiceCommand';
import FundTransfer from './FundTransfer';
import CreateUser from '../Admin/CreateUser';
import './Dashboard.css';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [balance, setBalance] = useState(0);
  const [accountNumber, setAccountNumber] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('overview');
  const [showVoiceTransactions, setShowVoiceTransactions] = useState(false); // NEW
  const navigate = useNavigate();

  // Wrap fetchBalance in useCallback
  const fetchBalance = useCallback(async () => {
    try {
      const data = await bankingService.getBalance();
      setBalance(data.balance);
      setAccountNumber(data.account_number);
    } catch (err) {
      console.error('Error fetching balance:', err);
    }
  }, []);

  // Wrap fetchTransactions in useCallback
  const fetchTransactions = useCallback(async () => {
    try {
      const data = await bankingService.getTransactions();
      setTransactions(data);
    } catch (err) {
      console.error('Error fetching transactions:', err);
    }
  }, []);

  // Wrap fetchDashboardData in useCallback
  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      await Promise.all([
        fetchBalance(),
        fetchTransactions()
      ]);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, [fetchBalance, fetchTransactions]);

  useEffect(() => {
    const username = localStorage.getItem('username');
    if (!username) {
      navigate('/login');
    } else {
      setUser({ username });
      fetchDashboardData();
    }
  }, [navigate, fetchDashboardData]);

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  const handleVoiceCommandProcessed = useCallback((result) => {
    console.log('Voice command result:', result);
    
    if (result.action === 'check_balance') {
      if (result.data?.balance !== undefined) {
        setBalance(result.data.balance);
        setAccountNumber(result.data.account_number);
        setMessage(`✅ ${result.message}`);
        setShowVoiceTransactions(false);
      }
    } else if (result.action === 'transfer') {
      if (result.data?.sender?.new_balance !== undefined) {
        setBalance(result.data.sender.new_balance);
        setMessage(`✅ ${result.message}`);
        fetchTransactions(); // Refresh transactions
        setShowVoiceTransactions(false);
        // Auto switch to overview tab to see updated transactions
        setActiveTab('overview');
      }
    } else if (result.action === 'transaction_history') {
      if (result.data?.transactions) {
        // Convert the transaction data to match our format
        const formattedTransactions = result.data.transactions.map(t => ({
          id: t.id,
          transaction_type: t.type,
          amount: t.amount,
          description: t.description,
          timestamp: t.timestamp,
          recipient_account: t.recipient_account || null
        }));
        
        setTransactions(formattedTransactions);
        setMessage(`✅ ${result.message}`);
        setShowVoiceTransactions(true);
        
        // Auto switch to overview tab to show transactions
        setActiveTab('overview');
      }
    } else if (result.action === 'unknown' || result.action === 'transfer_failed') {
      setError(`❌ ${result.message}`);
      if (result.suggestions) {
        setError(prev => prev + '\n\nSuggestions: ' + result.suggestions.join(', '));
      }
      setShowVoiceTransactions(false);
    }
    
    // Clear messages after 5 seconds
    setTimeout(() => {
      setMessage('');
      setError('');
    }, 5000);
  }, [fetchTransactions]);

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-content">
          <h1>🏦 Voice Banking System</h1>
          <div className="user-info">
            <span>Welcome, <strong>{user?.username}</strong></span>
            <button onClick={handleLogout} className="logout-btn">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button 
          className={`tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          📊 Overview
        </button>
        <button 
          className={`tab-btn ${activeTab === 'transfer' ? 'active' : ''}`}
          onClick={() => setActiveTab('transfer')}
        >
          💸 Transfer Funds
        </button>
        <button 
          className={`tab-btn ${activeTab === 'voice' ? 'active' : ''}`}
          onClick={() => setActiveTab('voice')}
        >
          🎤 Voice Commands
        </button>
        <button 
          className={`tab-btn ${activeTab === 'create-users' ? 'active' : ''}`}
          onClick={() => setActiveTab('create-users')}
        >
          🔧 Create Test Users
        </button>
      </div>

      {/* Messages */}
      {message && <div className="dashboard-message success">{message}</div>}
      {error && <div className="dashboard-message error">{error}</div>}

      <main className="dashboard-main">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <>
            {/* Account Summary */}
            <section className="account-summary">
              <div className="summary-card balance-card">
                <div className="card-icon">💰</div>
                <div className="card-content">
                  <h3>Current Balance</h3>
                  <p className="balance-amount">${balance.toFixed(2)}</p>
                </div>
              </div>
              <div className="summary-card account-card">
                <div className="card-icon">🏦</div>
                <div className="card-content">
                  <h3>Account Number</h3>
                  <p className="account-number">{accountNumber}</p>
                </div>
              </div>
              <div className="summary-card transactions-card">
                <div className="card-icon">📝</div>
                <div className="card-content">
                  <h3>Total Transactions</h3>
                  <p className="transaction-count">{transactions.length}</p>
                </div>
              </div>
            </section>

            {/* Recent Transactions */}
            <section className="transactions-section">
              <div className="section-header">
                <h2>{showVoiceTransactions ? 'Voice Command Results' : 'Recent Transactions'}</h2>
                {showVoiceTransactions && (
                  <button 
                    className="refresh-btn"
                    onClick={() => {
                      fetchTransactions();
                      setShowVoiceTransactions(false);
                    }}
                  >
                    🔄 Refresh All
                  </button>
                )}
              </div>
              
              {transactions.length === 0 ? (
                <div className="no-transactions">
                  <p>No transactions yet</p>
                  <p className="sub-text">Start by making a transfer or deposit</p>
                </div>
              ) : (
                <div className="transactions-list">
                  {transactions.map((transaction) => (
                    <div key={transaction.id} className="transaction-item">
                      <div className="transaction-icon">
                        {transaction.transaction_type === 'credit' ? '📥' : '📤'}
                      </div>
                      <div className="transaction-details">
                        <p className="transaction-description">{transaction.description}</p>
                        <p className="transaction-date">
                          {new Date(transaction.timestamp).toLocaleDateString()} at{' '}
                          {new Date(transaction.timestamp).toLocaleTimeString()}
                        </p>
                        {transaction.recipient_account && (
                          <p className="transaction-recipient">
                            To: {transaction.recipient_account}
                          </p>
                        )}
                      </div>
                      <div className={`transaction-amount ${transaction.transaction_type}`}>
                        {transaction.transaction_type === 'credit' ? '+' : '-'}$
                        {transaction.amount.toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}

        {/* Transfer Tab */}
        {activeTab === 'transfer' && (
          <section className="transfer-section">
            <FundTransfer />
          </section>
        )}

        {/* Voice Commands Tab */}
        {activeTab === 'voice' && (
          <section className="voice-section">
            <VoiceCommand onCommandProcessed={handleVoiceCommandProcessed} />
          </section>
        )}

        {/* Create Test Users Tab */}
        {activeTab === 'create-users' && (
          <section className="create-users-section">
            <CreateUser />
          </section>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
