import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AddInvestmentForm from '../components/AddInvestmentForm';

function Manage() {
  const navigate = useNavigate();

  const handleInvestmentAdded = () => {
    navigate('/portfolio');
  };

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: '64px' }}>
        <h1 style={{
          fontSize: '56px',
          fontWeight: 'bold',
          color: '#f9fafb',
          marginBottom: '16px'
        }}>
          Add Investment
        </h1>
        <p style={{ fontSize: '20px', color: '#9ca3af' }}>
          Add a new item to your portfolio
        </p>
      </div>

      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <AddInvestmentForm onInvestmentAdded={handleInvestmentAdded} />
      </div>
    </div>
  );
}

export default Manage;
