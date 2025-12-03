import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { bankingService } from '../../services/bankingService';
import { authService } from '../../services/authService';
import VoiceCommand from '../Voice/VoiceCommand';

const Dashboard = () => {
  const navigate = useNavigate();
  const [balance, setBalance] = useState(null);
  const [accountNumber, setAccountNumber] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [transferData, setTransferData] = useState({
    recipient_account: '',
    amount: '',
    description: ''
  });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      navigate('/login');
    } else {
      fetchBalance();
      fetchTransactions();
    }
  }, [navigate]);

  const fetchBalance = async () => {
    try {
      const data = await bankingService.getBalance();
      setBalance(data.balance);
      setAccountNumber(data.account_number);
    } catch (err) {
      setError('Failed to fetch balance');
    }
  };

  const fetchTransactions = async () => {
    try {
      const data = await bankingService.getTransactions();
      setTransactions(data);
    } catch (err) {
      console.error('Failed to fetch transactions');
    }
  };

  const handleTransfer = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');

    try {
      const result = await bankingService.transferFunds({
        ...transferData,
        amount: parseFloat(transferData.amount)
      });
      setMessage(`Transfer successful! New balance: $${result.new_balance}`);
      setTransferData({ recipient_account: '', amount: '', description: '' });
      fetchBalance();
      fetchTransactions();
    } catch (err) {
      setError(err.response?.data?.detail || 'Transfer failed');
    }
  };

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  const handleVoiceCommandProcessed = (result) => {
    if (result.action === 'check_balance') {
      setBalance(result.data.balance);
      setMessage(`Your balance is $${result.data.balance}`);
    } else if (result.action === 'transfer') {
      setMessage(`Transfer successful! New balance: $${result.data.new_balance}`);
      fetchBalance();
      fetchTransactions();
    }
  };

  return (
    <div className="dashboard">
      <header>
        <h1>Voice Banking Dashboard</h1>
        <button onClick={handleLogout}>Logout</button>
      </header>

      <VoiceCommand onCommandProcessed={handleVoiceCommandProcessed} />

      <section className="balance-section">
        <h2>Account Information</h2>
        <p><strong>Account Number:</strong> {accountNumber}</p>
        <p><strong>Balance:</strong> ${balance !== null ? balance.toFixed(2) : 'Loading...'}</p>
      </section>

      <section className="transfer-section">
        <h2>Fund Transfer</h2>
        <form onSubmit={handleTransfer}>
          <input
            type="text"
            placeholder="Recipient Account Number"
            value={transferData.recipient_account}
            onChange={(e) => setTransferData({...transferData, recipient_account: e.target.value})}
            required
          />
          <input
            type="number"
            step="0.01"
            placeholder="Amount"
            value={transferData.amount}
            onChange={(e) => setTransferData({...transferData, amount: e.target.value})}
            required
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={transferData.description}
            onChange={(e) => setTransferData({...transferData, description: e.target.value})}
          />
          <button type="submit">Transfer</button>
        </form>
      </section>

      <section className="transactions-section">
        <h2>Recent Transactions</h2>
        <table>
          <thead>
            <tr>
              <th>Type</th>
              <th>Amount</th>
              <th>Description</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((txn) => (
              <tr key={txn.id}>
                <td>{txn.transaction_type}</td>
                <td className={txn.transaction_type === 'credit' ? 'credit' : 'debit'}>
                  {txn.transaction_type === 'credit' ? '+' : '-'}${txn.amount.toFixed(2)}
                </td>
                <td>{txn.description}</td>
                <td>{new Date(txn.timestamp).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {message && <p className="success">{message}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
};

export default Dashboard;
