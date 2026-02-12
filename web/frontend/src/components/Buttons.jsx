import React from 'react';
import './Buttons.css';

export const GlowButton = ({ 
  children, 
  className = '', 
  size = 'md',
  ...props 
}) => {
  const sizeClass = size === 'sm' ? 'btn-sm' : size === 'lg' ? 'btn-lg' : '';
  return (
    <button 
      className={`glow-button ${sizeClass} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

export const SecondaryButton = ({ 
  children, 
  className = '', 
  size = 'md',
  ...props 
}) => {
  const sizeClass = size === 'sm' ? 'btn-sm' : size === 'lg' ? 'btn-lg' : '';
  return (
    <button 
      className={`secondary-button ${sizeClass} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

export const GhostButton = ({ 
  children, 
  className = '', 
  size = 'md',
  ...props 
}) => {
  const sizeClass = size === 'sm' ? 'btn-sm' : size === 'lg' ? 'btn-lg' : '';
  return (
    <button 
      className={`ghost-button ${sizeClass} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

export const IconButton = ({ 
  children, 
  className = '', 
  ...props 
}) => {
  return (
    <button 
      className={`icon-button ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};
