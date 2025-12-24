import React, { useState, useEffect } from 'react';
import { authService } from '../../services/authService';
import { bankingService } from '../../services/bankingService';
import './CreateUser.css';

const CreateUser = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: 'Test@123',
    full_name: ''
  });
  const [allUsers, setAllUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const quickUsers = [
    { username: 'alice', email: 'alice@test.com', full_name: 'Alice Johnson' },
    { username: 'bob', email: 'bob@test.com', full_name: 'Bob Smith' },
    { username: 'charlie', email: 'charlie@test.com', full_name: 'Charlie Brown' },
    { username: 'david', email: 'david@test.com', full_name: 'David Wilson' },
    { username: 'emma', email: 'emma@test.com', full_name: 'Emma Davis' }
  ];

  useEffect(() => {
    fetchAllUsers();
  }, []);

  const fetchAllUsers = async () => {
    try {
      setLoading(true);
      const response = await bankingService.getAllUsers();
      setAllUsers(response.users || []);
    } catch (err) {
      console.error('Failed to fetch users:', err);
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');

    try {
      await authService.register(formData);
      setSuccessMessage(`✅ User "${formData.username}" created successfully!`);
      setFormData({ username: '', email: '', password: 'Test@123', full_name: '' });
      
      // Refresh the users list
      await fetchAllUsers();
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create user');
    }
  };

  const createQuickUser = async (user) => {
    setError('');
    setSuccessMessage('');
    
    try {
      const userData = { ...user, password: 'Test@123' };
      await authService.register(userData);
      setSuccessMessage(`✅ User "${user.username}" created successfully!`);
      
      // Refresh the users list
      await fetchAllUsers();
      
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      setError(`Failed to create ${user.username}: ${err.response?.data?.detail || 'Unknown error'}`);
    }
  };

  const createAllQuickUsers = async () => {
    setError('');
    setSuccessMessage('Creating users...');
    
    let successCount = 0;
    let failCount = 0;
    
    for (const user of quickUsers) {
      try {
        const userData = { ...user, password: 'Test@123' };
        await authService.register(userData);
        successCount++;
        // Small delay between requests
        await new Promise(resolve => setTimeout(resolve, 500));
      } catch (err) {
        failCount++;
        console.error(`Failed to create ${user.username}:`, err.response?.data?.detail);
      }
    }
    
    // Refresh the users list
    await fetchAllUsers();
    
    if (failCount === 0) {
      setSuccessMessage(`✅ All ${successCount} users created successfully!`);
    } else {
      setSuccessMessage(`✅ Created ${successCount} users. ${failCount} already existed or failed.`);
    }
    
    setTimeout(() => setSuccessMessage(''), 5000);
  };

  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text);
    setSuccessMessage(`✅ ${label} copied to clipboard!`);
    setTimeout(() => setSuccessMessage(''), 2000);
  };

  const isUserAlreadyCreated = (username) => {
    return allUsers.some(u => u.username === username);
  };

  if (loading) {
    return (
      <div className="create-user-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading users...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="create-user-container">
      <div className="create-user-card">
        <h2>🔧 Create Test Users</h2>
        <p className="subtitle">Create recipient accounts for testing fund transfers</p>

        {/* Success/Error Messages */}
        {successMessage && <div className="success-message">{successMessage}</div>}
        {error && <div className="error-message">{error}</div>}

        {/* Quick Create Buttons */}
        <div className="quick-create-section">
          <h3>Quick Create</h3>
          <div className="quick-buttons">
            {quickUsers.map((user, index) => (
              <button
                key={index}
                onClick={() => createQuickUser(user)}
                className={`quick-btn ${isUserAlreadyCreated(user.username) ? 'created' : ''}`}
                disabled={isUserAlreadyCreated(user.username)}
              >
                {isUserAlreadyCreated(user.username) ? '✅' : '➕'} {user.username}
              </button>
            ))}
          </div>
          <button onClick={createAllQuickUsers} className="create-all-btn">
            Create All Test Users
          </button>
        </div>

        {/* Manual Create Form */}
        <div className="manual-create-section">
          <h3>Manual Create</h3>
          <form onSubmit={handleSubmit}>
            <input
              type="text"
              name="username"
              placeholder="Username"
              value={formData.username}
              onChange={handleChange}
              required
            />
            <input
              type="email"
              name="email"
              placeholder="Email"
              value={formData.email}
              onChange={handleChange}
              required
            />
            <input
              type="text"
              name="full_name"
              placeholder="Full Name"
              value={formData.full_name}
              onChange={handleChange}
            />
            <input
              type="password"
              name="password"
              placeholder="Password"
              value={formData.password}
              onChange={handleChange}
              required
            />
            <button type="submit">Create User</button>
          </form>
        </div>

        {/* All Users List */}
        <div className="all-users-section">
          <div className="section-header">
            <h3>📋 All Available Users ({allUsers.length})</h3>
            <button onClick={fetchAllUsers} className="refresh-btn">
              🔄 Refresh
            </button>
          </div>
          
          {allUsers.length === 0 ? (
            <div className="no-users">
              <p>No users created yet</p>
              <p className="sub-text">Create some test users to get started</p>
            </div>
          ) : (
            <div className="users-list">
              {allUsers.map((user, index) => (
                <div key={index} className="user-card">
                  <div className="user-avatar">{user.username.charAt(0).toUpperCase()}</div>
                  <div className="user-info">
                    <strong>{user.username}</strong>
                    {user.full_name && <span className="user-full-name">{user.full_name}</span>}
                    <span className="user-email">{user.email}</span>
                    <code className="account-number">{user.account_number}</code>
                    <span className="balance">Balance: ${user.balance.toFixed(2)}</span>
                  </div>
                  <div className="user-actions">
                    <button 
                      className="copy-btn"
                      onClick={() => copyToClipboard(user.account_number, 'Account number')}
                      title="Copy account number"
                    >
                      📋 Copy Account
                    </button>
                    <button 
                      className="copy-btn secondary"
                      onClick={() => copyToClipboard(user.username, 'Username')}
                      title="Copy username"
                    >
                      👤 Copy Username
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="instructions">
          <h4>💡 How to Use:</h4>
          <ol>
            <li>Create test users using quick buttons or manual form</li>
            <li>Copy account numbers or usernames for transfers</li>
            <li>Use in fund transfer form or voice commands:
              <ul>
                <li>"Transfer 100 to user bob"</li>
                <li>"Send 50 to ACC..." (paste account number)</li>
              </ul>
            </li>
            <li>All users start with $1,000 balance</li>
            <li>Default password for quick users: <code>Test@123</code></li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default CreateUser;
