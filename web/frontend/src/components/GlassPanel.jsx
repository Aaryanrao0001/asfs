import React from 'react';
import './GlassPanel.css';

export const GlassPanel = ({ 
  children, 
  className = '', 
  interactive = false,
  ...props 
}) => {
  return (
    <div 
      className={`glass-panel ${interactive ? 'interactive' : ''} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const GlassPanelHeader = ({ children, className = '' }) => {
  return (
    <div className={`glass-panel-header ${className}`}>
      {children}
    </div>
  );
};

export const GlassPanelBody = ({ children, className = '' }) => {
  return (
    <div className={`glass-panel-body ${className}`}>
      {children}
    </div>
  );
};

export const GlassPanelFooter = ({ children, className = '' }) => {
  return (
    <div className={`glass-panel-footer ${className}`}>
      {children}
    </div>
  );
};
