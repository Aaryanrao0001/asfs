import React from 'react';
import { Link, NavLink } from 'react-router-dom';
import { Shield } from 'lucide-react';
import './Layout.css';

export const Layout = ({ children }) => {
  return (
    <div className="app-layout">
      <TopNav />
      <div className="content-wrapper">
        <MainContent>{children}</MainContent>
      </div>
    </div>
  );
};

const TopNav = () => {
  const tabs = [
    { path: '/input', label: 'Input' },
    { path: '/ai', label: 'AI' },
    { path: '/metadata', label: 'Metadata' },
    { path: '/upload', label: 'Upload' },
    { path: '/videos', label: 'Videos' },
    { path: '/run', label: 'Run' }
  ];

  return (
    <nav className="top-nav">
      <div className="top-nav-left">
        <Link to="/" className="nav-logo">
          <Shield className="nav-logo-icon" />
          <span>ASFS</span>
        </Link>
        
        <ul className="nav-tabs">
          {tabs.map((tab) => (
            <li key={tab.path}>
              <NavLink 
                to={tab.path} 
                className={({ isActive }) => `nav-tab ${isActive ? 'active' : ''}`}
              >
                {tab.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
      
      <div className="top-nav-right">
        {/* Placeholder for future features */}
      </div>
    </nav>
  );
};

const MainContent = ({ children }) => {
  return (
    <main className="main-content">
      {children}
    </main>
  );
};
