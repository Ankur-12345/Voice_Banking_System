import React, { useState } from 'react';
import { authService } from '../../services/authService';
import './CreateUser.css';

const CreateUser = () => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: 'Test@123',
    full_name: ''
  });
  const [createdUsers, setCreatedUsers] = useState([]);
  const [error, setError] = useState('');

  const quickUsers = [
    { username: 'alice', email: 'alice@test.com', full_name: 'Alice Johnson' },
    { username: 'bob', email: 'bob@test.com', full_name: 'Bob Smith' },
    { username: 'charlie', email: 'charlie@test.com', full_name: 'Charlie Brown' },
    { username: 'david', email: 'david@test.com', full_name: 'David Wilson' },
    { username: 'emma', email: 'emma@test.com', full_name: 'Emma Davis' }
  ];

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await authService.register(formData);
      setCreatedUsers([...createdUsers, response]);
      setFormData({ username: '', email: '', password: 'Test@123', full_name: '' });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create user');
    }
  };

  const createQuickUser = async (user) => {
    try {
      const userData = { ...user, password: 'Test@123' };
      const response = await authService.register(userData);
      setCreatedUsers([...createdUsers, response]);
    } catch (err) {
      setError(`Failed to create ${user.username}: ${err.response?.data?.detail || 'Unknown error'}`);
    }
  };

  const createAllQuickUsers = async () => {
    for (const user of quickUsers) {
      await createQuickUser(user);
      // Small delay between requests
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  };

  return (
    <div className="create-user-container">
      <div className="create-user-card">
        <h2>🔧 Create Test Users</h2>
        <p className="subtitle">Create recipient accounts for testing fund transfers</p>

        {/* Quick Create Buttons */}
        <div className="quick-create-section">
          <h3>Quick Create</h3>
          <div className="quick-buttons">
            {quickUsers.map((user, index) => (
              <button
                key={index}
                onClick={() => createQuickUser(user)}
                className="quick-btn"
                disabled={createdUsers.some(u => u.username === user.username)}
              >
                {createdUsers.some(u => u.username === user.username) ? '✅' : '➕'} {user.username}
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

        {error && <div className="error-message">{error}</div>}

        {/* Created Users List */}
        {createdUsers.length > 0 && (
          <div className="created-users-section">
            <h3>✅ Created Users ({createdUsers.length})</h3>
            <div className="users-list">
              {createdUsers.map((user, index) => (
                <div key={index} className="user-card">
                  <div className="user-avatar">{user.username.charAt(0).toUpperCase()}</div>
                  <div className="user-info">
                    <strong>{user.username}</strong>
                    <span className="user-email">{user.email}</span>
                    <code className="account-number">{user.account_number}</code>
                    <span className="balance">Balance: ${user.balance.toFixed(2)}</span>
                  </div>
                  <button 
                    className="copy-btn"
                    onClick={() => {
                      navigator.clipboard.writeText(user.account_number);
                      alert('Account number copied!');
                    }}
                  >
                    📋 Copy
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="instructions">
          <h4>💡 How to Use:</h4>
          <ol>
            <li>Create test users using quick buttons or manual form</li>
            <li>Copy account numbers for transfers</li>
            <li>Use voice commands:
              <ul>
                <li>"Transfer 100 to user bob"</li>
                <li>"Send 50 to ACC..." (paste account number)</li>
              </ul>
            </li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default CreateUser;
