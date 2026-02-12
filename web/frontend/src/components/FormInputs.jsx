import React from 'react';
import './FormInputs.css';

export const TextInput = ({ 
  label, 
  helper, 
  error, 
  className = '', 
  ...props 
}) => {
  return (
    <div className="form-group">
      {label && <label className="form-label">{label}</label>}
      <input 
        type="text"
        className={`text-input ${className}`}
        {...props}
      />
      {helper && <div className="form-helper">{helper}</div>}
      {error && <div className="form-error">{error}</div>}
    </div>
  );
};

export const TextArea = ({ 
  label, 
  helper, 
  error, 
  className = '', 
  ...props 
}) => {
  return (
    <div className="form-group">
      {label && <label className="form-label">{label}</label>}
      <textarea 
        className={`text-area ${className}`}
        {...props}
      />
      {helper && <div className="form-helper">{helper}</div>}
      {error && <div className="form-error">{error}</div>}
    </div>
  );
};

export const Select = ({ 
  label, 
  helper, 
  error, 
  options = [], 
  className = '', 
  ...props 
}) => {
  return (
    <div className="form-group">
      {label && <label className="form-label">{label}</label>}
      <select 
        className={`select-input ${className}`}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {helper && <div className="form-helper">{helper}</div>}
      {error && <div className="form-error">{error}</div>}
    </div>
  );
};

export const Checkbox = ({ 
  label, 
  className = '', 
  ...props 
}) => {
  return (
    <label className={`checkbox-container ${className}`}>
      <input 
        type="checkbox"
        className="checkbox-input"
        {...props}
      />
      {label && <span className="checkbox-label">{label}</span>}
    </label>
  );
};

export const Radio = ({ 
  label, 
  className = '', 
  ...props 
}) => {
  return (
    <label className={`radio-container ${className}`}>
      <input 
        type="radio"
        className="radio-input"
        {...props}
      />
      {label && <span className="radio-label">{label}</span>}
    </label>
  );
};

export const Toggle = ({ 
  label, 
  className = '', 
  ...props 
}) => {
  return (
    <label className={`toggle-container ${className}`}>
      <input 
        type="checkbox"
        className="toggle-input"
        {...props}
      />
      {label && <span className="toggle-label">{label}</span>}
    </label>
  );
};
