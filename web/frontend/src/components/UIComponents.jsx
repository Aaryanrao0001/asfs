import React from 'react';
import './UIComponents.css';

export const ProgressBar = ({ value = 0, max = 100 }) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  
  return (
    <div className="progress-container">
      <div 
        className="progress-bar" 
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
};

export const StatusBadge = ({ status, children }) => {
  const statusClass = status || 'info';
  
  return (
    <span className={`status-badge ${statusClass}`}>
      {children}
    </span>
  );
};

export const LogViewer = ({ logs = [] }) => {
  return (
    <div className="log-viewer">
      {logs.map((log, index) => (
        <div key={index} className={`log-entry ${log.level?.toLowerCase() || 'info'}`}>
          <span className="timestamp">{log.timestamp}</span>
          {log.message}
        </div>
      ))}
      {logs.length === 0 && (
        <div className="log-entry info">No logs yet...</div>
      )}
    </div>
  );
};

export const Tooltip = ({ content, children }) => {
  return (
    <div className="tooltip">
      {children}
      <div className="tooltip-content">{content}</div>
    </div>
  );
};

export const Modal = ({ isOpen, onClose, title, children, footer }) => {
  if (!isOpen) return null;
  
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="icon-button" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          {children}
        </div>
        {footer && (
          <div className="modal-footer">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};
