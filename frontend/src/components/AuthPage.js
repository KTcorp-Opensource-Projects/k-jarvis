import React, { useState, useEffect } from 'react';
import { useStore } from '../store';

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [rotation, setRotation] = useState(0);
  
  const { login, register, authLoading, authError, clearAuthError } = useStore();
  
  // Logo rotation animation
  useEffect(() => {
    const interval = setInterval(() => {
      setRotation(prev => (prev + 0.5) % 360);
    }, 50);
    return () => clearInterval(interval);
  }, []);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    clearAuthError();
    
    if (isLogin) {
      const result = await login(username, password);
      if (result.success) {
        // Login successful
      }
    } else {
      const result = await register(username, email, password, name);
      if (result.success) {
        setShowSuccess(true);
        setIsLogin(true);
        setPassword('');
        setUsername('');
        setTimeout(() => setShowSuccess(false), 3000);
      }
    }
  };
  
  const switchMode = () => {
    setIsLogin(!isLogin);
    clearAuthError();
    setShowSuccess(false);
  };

  return (
    <div style={styles.container}>
      {/* Animated background grid */}
      <div style={styles.gridOverlay} />
      
      {/* Floating particles */}
      <div style={styles.particles}>
        {[...Array(20)].map((_, i) => (
          <div 
            key={i} 
            style={{
              ...styles.particle,
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 5}s`,
              animationDuration: `${3 + Math.random() * 4}s`
            }}
          />
        ))}
      </div>
      
      {/* Scanline effect */}
      <div style={styles.scanline} />
      
      <div style={styles.card}>
        {/* HUD Corner brackets */}
        <div style={{...styles.corner, ...styles.cornerTL}} />
        <div style={{...styles.corner, ...styles.cornerTR}} />
        <div style={{...styles.corner, ...styles.cornerBL}} />
        <div style={{...styles.corner, ...styles.cornerBR}} />
        
        {/* J.A.R.V.I.S Logo */}
        <div style={styles.logoSection}>
          <div style={styles.logoContainer}>
            {/* Outer rotating ring */}
            <div style={{...styles.logoRing, ...styles.logoRingOuter, transform: `rotate(${rotation}deg)`}}>
              <svg viewBox="0 0 200 200" style={styles.logoSvg}>
                <defs>
                  <linearGradient id="ringGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#00d4ff" />
                    <stop offset="50%" stopColor="#00fff7" />
                    <stop offset="100%" stopColor="#00b8d4" />
                  </linearGradient>
                </defs>
                <circle cx="100" cy="100" r="95" fill="none" stroke="url(#ringGrad)" strokeWidth="2" strokeDasharray="15 5" />
                <circle cx="100" cy="100" r="85" fill="none" stroke="rgba(0,212,255,0.3)" strokeWidth="1" />
              </svg>
            </div>
            
            {/* Middle ring - counter rotate */}
            <div style={{...styles.logoRing, ...styles.logoRingMiddle, transform: `rotate(${-rotation * 1.5}deg)`}}>
              <svg viewBox="0 0 160 160" style={styles.logoSvg}>
                <circle cx="80" cy="80" r="75" fill="none" stroke="rgba(0,212,255,0.5)" strokeWidth="1" strokeDasharray="8 4" />
                {/* Tech marks */}
                {[0, 45, 90, 135, 180, 225, 270, 315].map((angle, i) => (
                  <line 
                    key={i}
                    x1={80 + 60 * Math.cos(angle * Math.PI / 180)}
                    y1={80 + 60 * Math.sin(angle * Math.PI / 180)}
                    x2={80 + 70 * Math.cos(angle * Math.PI / 180)}
                    y2={80 + 70 * Math.sin(angle * Math.PI / 180)}
                    stroke="#00d4ff"
                    strokeWidth="2"
                  />
                ))}
              </svg>
            </div>
            
            {/* Inner core */}
            <div style={styles.logoCore}>
              <div style={styles.logoCoreInner}>
                <span style={styles.logoText}>K</span>
              </div>
            </div>
          </div>
          
          <h1 style={styles.title}>K-JARVIS</h1>
          <p style={styles.subtitle}>KT AI AGENT PLATFORM</p>
          <div style={styles.statusBar}>
            <span style={styles.statusDot} />
            <span style={styles.statusText}>SYSTEM ONLINE</span>
          </div>
        </div>
        
        {/* Success Message */}
        {showSuccess && (
          <div style={styles.successMessage}>
            <span style={styles.messageIcon}>✓</span> 
            <span>REGISTRATION COMPLETE. PLEASE LOGIN.</span>
          </div>
        )}
        
        {/* Error Message */}
        {authError && (
          <div style={styles.errorMessage}>
            <span style={styles.messageIcon}>⚠</span> 
            <span>{authError}</span>
          </div>
        )}
        
        {/* Form */}
        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.formHeader}>
            <div style={styles.formHeaderLine} />
            <h2 style={styles.formTitle}>
              {isLogin ? 'AUTHENTICATION' : 'REGISTRATION'}
            </h2>
            <div style={styles.formHeaderLine} />
          </div>
          
          {!isLogin && (
            <>
              <div style={styles.inputGroup}>
                <label style={styles.label}>NAME</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your name"
                  style={styles.input}
                  required
                  minLength={2}
                />
              </div>
              
              <div style={styles.inputGroup}>
                <label style={styles.label}>USER ID</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter user ID"
                  style={styles.input}
                  required
                  minLength={3}
                />
              </div>
              
              <div style={styles.inputGroup}>
                <label style={styles.label}>EMAIL</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="email@example.com"
                  style={styles.input}
                  required
                />
              </div>
            </>
          )}
          
          {isLogin && (
            <div style={styles.inputGroup}>
              <label style={styles.label}>USER ID / EMAIL</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                style={styles.input}
                required
                autoComplete="off"
              />
            </div>
          )}
          
          <div style={styles.inputGroup}>
            <label style={styles.label}>PASSWORD</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={styles.input}
              required
              minLength={6}
              autoComplete="new-password"
            />
          </div>
          
          <button 
            type="submit" 
            style={{
              ...styles.submitButton,
              ...(authLoading && styles.submitButtonDisabled)
            }}
            disabled={authLoading}
          >
            {authLoading ? (
              <span style={styles.loadingText}>PROCESSING...</span>
            ) : (
              <>
                <span style={styles.buttonIcon}>{isLogin ? '▶' : '+'}</span>
                <span>{isLogin ? 'INITIATE LOGIN' : 'CREATE ACCOUNT'}</span>
              </>
            )}
          </button>
          
          {isLogin && (
            <>
              <div style={styles.divider}>
                <span style={styles.dividerLine} />
                <span style={styles.dividerText}>OR</span>
                <span style={styles.dividerLine} />
              </div>
              
              <button 
                type="button"
                onClick={() => window.location.href = `${process.env.REACT_APP_API_URL || 'http://localhost:4001'}/auth/kauth`}
                style={styles.kauthButton}
              >
                <span style={styles.kauthIcon}>🔐</span>
                <span>K-AUTH SSO LOGIN</span>
              </button>
            </>
          )}
        </form>
        
        {/* Switch Mode */}
        <div style={styles.switchSection}>
          <span style={styles.switchText}>
            {isLogin ? 'NEW USER?' : 'EXISTING USER?'}
          </span>
          <button onClick={switchMode} style={styles.switchButton}>
            {isLogin ? 'REGISTER' : 'LOGIN'}
          </button>
        </div>
      </div>
      
      {/* Version info */}
      <div style={styles.versionInfo}>
        <span>K-JARVIS v2.0.0</span>
        <span style={styles.versionDivider}>|</span>
        <span>A2A PROTOCOL</span>
      </div>
    </div>
  );
};

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(180deg, #020810 0%, #051020 50%, #0a1828 100%)',
    padding: '20px',
    position: 'relative',
    overflow: 'hidden',
    fontFamily: "'Rajdhani', 'Orbitron', sans-serif",
  },
  gridOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundImage: `
      linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px)
    `,
    backgroundSize: '60px 60px',
    pointerEvents: 'none',
  },
  particles: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    pointerEvents: 'none',
    overflow: 'hidden',
  },
  particle: {
    position: 'absolute',
    width: '4px',
    height: '4px',
    background: 'rgba(0, 212, 255, 0.6)',
    borderRadius: '50%',
    boxShadow: '0 0 10px rgba(0, 212, 255, 0.8)',
    animation: 'float 5s ease-in-out infinite',
  },
  scanline: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: '2px',
    background: 'linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.5), transparent)',
    animation: 'scanline 6s linear infinite',
    pointerEvents: 'none',
  },
  card: {
    width: '100%',
    maxWidth: '440px',
    background: 'rgba(5, 20, 35, 0.85)',
    border: '1px solid rgba(0, 212, 255, 0.3)',
    borderRadius: '4px',
    padding: '40px',
    backdropFilter: 'blur(20px)',
    position: 'relative',
    zIndex: 1,
    boxShadow: `
      0 0 40px rgba(0, 212, 255, 0.15),
      inset 0 0 60px rgba(0, 212, 255, 0.03)
    `,
  },
  corner: {
    position: 'absolute',
    width: '25px',
    height: '25px',
    border: '2px solid #00d4ff',
  },
  cornerTL: { top: -1, left: -1, borderRight: 'none', borderBottom: 'none' },
  cornerTR: { top: -1, right: -1, borderLeft: 'none', borderBottom: 'none' },
  cornerBL: { bottom: -1, left: -1, borderRight: 'none', borderTop: 'none' },
  cornerBR: { bottom: -1, right: -1, borderLeft: 'none', borderTop: 'none' },
  logoSection: {
    textAlign: 'center',
    marginBottom: '32px',
  },
  logoContainer: {
    width: '140px',
    height: '140px',
    margin: '0 auto 20px',
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoRing: {
    position: 'absolute',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoRingOuter: {
    width: '140px',
    height: '140px',
  },
  logoRingMiddle: {
    width: '110px',
    height: '110px',
  },
  logoSvg: {
    width: '100%',
    height: '100%',
  },
  logoCore: {
    width: '70px',
    height: '70px',
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(0, 212, 255, 0.2) 0%, rgba(5, 20, 35, 0.9) 70%)',
    border: '2px solid rgba(0, 212, 255, 0.6)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    boxShadow: `
      0 0 30px rgba(0, 212, 255, 0.4),
      inset 0 0 20px rgba(0, 212, 255, 0.2)
    `,
    zIndex: 1,
  },
  logoCoreInner: {
    width: '50px',
    height: '50px',
    borderRadius: '50%',
    background: 'rgba(0, 20, 40, 0.8)',
    border: '1px solid rgba(0, 212, 255, 0.4)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '28px',
    fontWeight: '700',
    color: '#00d4ff',
    textShadow: '0 0 20px rgba(0, 212, 255, 0.8)',
  },
  title: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '32px',
    fontWeight: '700',
    color: '#00d4ff',
    marginBottom: '8px',
    letterSpacing: '8px',
    textShadow: '0 0 30px rgba(0, 212, 255, 0.6)',
  },
  subtitle: {
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '12px',
    color: '#4a9eb8',
    letterSpacing: '4px',
    marginBottom: '12px',
  },
  statusBar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    background: '#00ff88',
    boxShadow: '0 0 10px rgba(0, 255, 136, 0.8)',
    animation: 'pulse 2s ease-in-out infinite',
  },
  statusText: {
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '10px',
    color: '#00ff88',
    letterSpacing: '2px',
  },
  successMessage: {
    padding: '12px 16px',
    background: 'rgba(0, 255, 136, 0.1)',
    border: '1px solid rgba(0, 255, 136, 0.4)',
    borderRadius: '4px',
    color: '#00ff88',
    fontSize: '12px',
    marginBottom: '20px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontFamily: "'Share Tech Mono', monospace",
    letterSpacing: '1px',
  },
  errorMessage: {
    padding: '12px 16px',
    background: 'rgba(255, 61, 61, 0.1)',
    border: '1px solid rgba(255, 61, 61, 0.4)',
    borderRadius: '4px',
    color: '#ff3d3d',
    fontSize: '12px',
    marginBottom: '20px',
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    fontFamily: "'Share Tech Mono', monospace",
    letterSpacing: '1px',
  },
  messageIcon: {
    fontSize: '16px',
  },
  form: {
    marginBottom: '24px',
  },
  formHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    marginBottom: '24px',
  },
  formHeaderLine: {
    flex: 1,
    height: '1px',
    background: 'linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.5), transparent)',
  },
  formTitle: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '14px',
    fontWeight: '600',
    color: '#00d4ff',
    letterSpacing: '3px',
  },
  inputGroup: {
    marginBottom: '20px',
  },
  label: {
    display: 'block',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '11px',
    fontWeight: '500',
    color: '#4a9eb8',
    marginBottom: '8px',
    letterSpacing: '2px',
  },
  input: {
    width: '100%',
    padding: '14px 16px',
    background: 'rgba(0, 20, 40, 0.6)',
    border: '1px solid rgba(0, 212, 255, 0.2)',
    borderRadius: '4px',
    color: '#e0f7ff',
    fontSize: '14px',
    fontFamily: "'Rajdhani', sans-serif",
    outline: 'none',
    transition: 'all 0.3s ease',
    boxSizing: 'border-box',
  },
  submitButton: {
    width: '100%',
    padding: '16px 24px',
    background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(0, 184, 212, 0.2) 100%)',
    border: '1px solid rgba(0, 212, 255, 0.5)',
    borderRadius: '4px',
    color: '#00d4ff',
    fontSize: '14px',
    fontFamily: "'Orbitron', sans-serif",
    fontWeight: '600',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    transition: 'all 0.3s ease',
    marginTop: '8px',
    letterSpacing: '2px',
    textTransform: 'uppercase',
  },
  submitButtonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
  buttonIcon: {
    fontSize: '12px',
  },
  loadingText: {
    animation: 'pulse 1s ease-in-out infinite',
  },
  switchSection: {
    textAlign: 'center',
    paddingTop: '20px',
    borderTop: '1px solid rgba(0, 212, 255, 0.15)',
  },
  switchText: {
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '12px',
    color: '#4a9eb8',
    letterSpacing: '1px',
  },
  switchButton: {
    background: 'none',
    border: 'none',
    color: '#00d4ff',
    fontSize: '12px',
    fontFamily: "'Orbitron', sans-serif",
    fontWeight: '600',
    cursor: 'pointer',
    marginLeft: '8px',
    letterSpacing: '2px',
    textDecoration: 'underline',
    textUnderlineOffset: '3px',
  },
  versionInfo: {
    position: 'absolute',
    bottom: '20px',
    left: '50%',
    transform: 'translateX(-50%)',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '10px',
    color: '#2d6880',
    letterSpacing: '2px',
    display: 'flex',
    gap: '12px',
  },
  versionDivider: {
    color: 'rgba(0, 212, 255, 0.3)',
  },
  divider: {
    display: 'flex',
    alignItems: 'center',
    gap: '16px',
    margin: '24px 0',
  },
  dividerLine: {
    flex: 1,
    height: '1px',
    background: 'linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.3), transparent)',
  },
  dividerText: {
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '11px',
    color: '#4a9eb8',
    letterSpacing: '2px',
  },
  kauthButton: {
    width: '100%',
    padding: '16px 24px',
    background: 'linear-gradient(135deg, rgba(138, 43, 226, 0.2) 0%, rgba(75, 0, 130, 0.2) 100%)',
    border: '1px solid rgba(138, 43, 226, 0.5)',
    borderRadius: '4px',
    color: '#9966ff',
    fontSize: '14px',
    fontFamily: "'Orbitron', sans-serif",
    fontWeight: '600',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    transition: 'all 0.3s ease',
    letterSpacing: '2px',
    textTransform: 'uppercase',
  },
  kauthIcon: {
    fontSize: '16px',
  },
};

// Add keyframe animations and input focus styles
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
  @keyframes float {
    0%, 100% { transform: translateY(0px) translateX(0px); opacity: 0.6; }
    25% { transform: translateY(-20px) translateX(10px); opacity: 1; }
    50% { transform: translateY(-10px) translateX(-5px); opacity: 0.8; }
    75% { transform: translateY(-30px) translateX(5px); opacity: 0.6; }
  }
  @keyframes scanline {
    0% { top: -10%; }
    100% { top: 110%; }
  }
  input:focus {
    border-color: rgba(0, 212, 255, 0.6) !important;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.2), inset 0 0 10px rgba(0, 212, 255, 0.05) !important;
  }
  input::placeholder {
    color: #2d6880;
  }
  button:hover:not(:disabled) {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.3) 0%, rgba(0, 184, 212, 0.3) 100%) !important;
    box-shadow: 0 0 30px rgba(0, 212, 255, 0.3), inset 0 0 20px rgba(0, 212, 255, 0.1) !important;
    transform: translateY(-1px);
  }
`;
document.head.appendChild(styleSheet);

export default AuthPage;
