import React, { useState, useEffect } from 'react';
import { useStore } from '../store';

const AdminPanel = () => {
  const {
    agents,
    fetchAgents,
    registerAgentByUrl,
    unregisterAgent,
    isRegistering,
    registrationError,
    clearRegistrationError
  } = useStore();
  
  const [newAgentUrl, setNewAgentUrl] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  
  useEffect(() => {
    fetchAgents();
    const interval = setInterval(fetchAgents, 30000);
    return () => clearInterval(interval);
  }, [fetchAgents]);
  
  const handleRegister = async (e) => {
    e.preventDefault();
    if (!newAgentUrl.trim()) return;
    
    const result = await registerAgentByUrl(newAgentUrl.trim());
    if (result.success) {
      setNewAgentUrl('');
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    }
  };
  
  const handleDelete = async (agentId) => {
    const result = await unregisterAgent(agentId);
    if (result.success) {
      setDeleteConfirm(null);
    }
  };
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return '#00ff88';
      case 'offline': return '#ff3d3d';
      case 'busy': return '#ffb300';
      default: return '#4a9eb8';
    }
  };
  
  const getStatusIcon = (status) => {
    switch (status) {
      case 'online': return '●';
      case 'offline': return '○';
      case 'busy': return '◐';
      default: return '?';
    }
  };

  return (
    <div style={styles.container}>
      {/* Grid overlay */}
      <div style={styles.gridOverlay} />
      
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>AGENT MANAGEMENT</h1>
        <p style={styles.subtitle}>
          REGISTER AND MANAGE AI AGENTS
        </p>
      </div>
      
      {/* Agent Registration Form */}
      <div style={styles.registrationCard}>
        {/* HUD corners */}
        <div style={{...styles.corner, ...styles.cornerTL}} />
        <div style={{...styles.corner, ...styles.cornerTR}} />
        <div style={{...styles.corner, ...styles.cornerBL}} />
        <div style={{...styles.corner, ...styles.cornerBR}} />
        
        <h2 style={styles.cardTitle}>
          <span style={styles.icon}>➕</span>
          REGISTER NEW AGENT
        </h2>
        <p style={styles.cardDescription}>
          Enter the AI agent server URL. The system will automatically fetch agent information.
        </p>
        
        <form onSubmit={handleRegister} style={styles.form}>
          <div style={styles.inputGroup}>
            <input
              type="url"
              value={newAgentUrl}
              onChange={(e) => {
                setNewAgentUrl(e.target.value);
                clearRegistrationError();
              }}
              placeholder="http://localhost:8001"
              style={styles.input}
              disabled={isRegistering}
            />
            <button 
              type="submit" 
              style={{
                ...styles.registerButton,
                ...(isRegistering && styles.registerButtonDisabled)
              }}
              disabled={isRegistering || !newAgentUrl.trim()}
            >
              {isRegistering ? (
                <>
                  <span style={styles.spinner}>⟳</span>
                  CONNECTING...
                </>
              ) : (
                'REGISTER AGENT'
              )}
            </button>
          </div>
          
          {registrationError && (
            <div style={styles.errorMessage}>
              <span>⚠</span> {registrationError}
            </div>
          )}
          
          {showSuccess && (
            <div style={styles.successMessage}>
              <span>✓</span> AGENT REGISTERED SUCCESSFULLY
            </div>
          )}
        </form>
        
        <div style={styles.tips}>
          <h4 style={styles.tipsTitle}>💡 HELP</h4>
          <ul style={styles.tipsList}>
            <li>Ensure the agent server is running before registration</li>
            <li>Example URL: <code style={styles.code}>http://localhost:5010</code></li>
          </ul>
        </div>
      </div>
      
      {/* Registered Agents List */}
      <div style={styles.agentsSection}>
        <div style={{...styles.corner, ...styles.cornerTL}} />
        <div style={{...styles.corner, ...styles.cornerTR}} />
        <div style={{...styles.corner, ...styles.cornerBL}} />
        <div style={{...styles.corner, ...styles.cornerBR}} />
        
        <div style={styles.agentsSectionHeader}>
          <h2 style={styles.cardTitle}>
            <span style={styles.icon}>🤖</span>
            REGISTERED AGENTS
          </h2>
          <span style={styles.agentCount}>
            {agents.length} ACTIVE
          </span>
        </div>
        
        {agents.length === 0 ? (
          <div style={styles.emptyState}>
            <div style={styles.emptyIcon}>📭</div>
            <p style={styles.emptyText}>NO AGENTS REGISTERED</p>
            <p style={styles.emptySubtext}>
              Use the form above to register your first agent
            </p>
          </div>
        ) : (
          <div style={styles.agentsList}>
            {agents.map((agent) => (
              <div key={agent.id} style={styles.agentCard}>
                <div style={styles.agentHeader}>
                  <div style={styles.agentInfo}>
                    <div style={styles.agentNameRow}>
                      <span 
                        style={{
                          ...styles.statusIndicator,
                          color: getStatusColor(agent.status),
                          textShadow: `0 0 10px ${getStatusColor(agent.status)}`
                        }}
                      >
                        {getStatusIcon(agent.status)}
                      </span>
                      <h3 style={styles.agentName}>{agent.name}</h3>
                      <span style={styles.version}>v{agent.version}</span>
                    </div>
                    <p style={styles.agentDescription}>{agent.description}</p>
                    <div style={styles.agentUrl}>
                      <span style={styles.urlLabel}>URL:</span>
                      <code style={styles.urlValue}>{agent.url}</code>
                    </div>
                  </div>
                  
                  <div style={styles.agentActions}>
                    <button
                      style={styles.refreshButton}
                      onClick={() => registerAgentByUrl(agent.url)}
                      title="Refresh agent info"
                    >
                      ↻
                    </button>
                    <button
                      style={styles.deleteButton}
                      onClick={() => setDeleteConfirm(agent.id)}
                      title="Remove agent"
                    >
                      🗑
                    </button>
                  </div>
                </div>
                
                {/* Skills */}
                {agent.skills && agent.skills.length > 0 && (
                  <div style={styles.skillsSection}>
                    <h4 style={styles.skillsTitle}>SKILLS</h4>
                    <div style={styles.skillsList}>
                      {agent.skills.map((skill, idx) => (
                        <div key={idx} style={styles.skillTag}>
                          <span style={styles.skillName}>{skill.name}</span>
                          {skill.tags && skill.tags.length > 0 && (
                            <div style={styles.skillTags}>
                              {skill.tags.slice(0, 3).map((tag, tidx) => (
                                <span key={tidx} style={styles.tag}>{tag}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Capabilities */}
                <div style={styles.capabilitiesRow}>
                  {agent.capabilities?.streaming && (
                    <span style={styles.capability}>🔄 STREAMING</span>
                  )}
                  {agent.capabilities?.pushNotifications && (
                    <span style={styles.capability}>🔔 PUSH</span>
                  )}
                </div>
                
                {/* Delete Confirmation */}
                {deleteConfirm === agent.id && (
                  <div style={styles.deleteConfirmOverlay}>
                    <div style={styles.deleteConfirmBox}>
                      <p>DELETE <strong>{agent.name}</strong>?</p>
                      <div style={styles.deleteConfirmActions}>
                        <button 
                          style={styles.cancelButton}
                          onClick={() => setDeleteConfirm(null)}
                        >
                          CANCEL
                        </button>
                        <button 
                          style={styles.confirmDeleteButton}
                          onClick={() => handleDelete(agent.id)}
                        >
                          DELETE
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const styles = {
  container: {
    flex: 1,
    padding: '32px',
    overflowY: 'auto',
    background: 'linear-gradient(180deg, #020810 0%, #051020 50%, #0a1828 100%)',
    minHeight: '100vh',
    position: 'relative',
    fontFamily: "'Rajdhani', 'Orbitron', sans-serif",
  },
  gridOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundImage: `
      linear-gradient(rgba(0, 212, 255, 0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 212, 255, 0.02) 1px, transparent 1px)
    `,
    backgroundSize: '50px 50px',
    pointerEvents: 'none',
  },
  header: {
    marginBottom: '32px',
    position: 'relative',
    zIndex: 1,
  },
  title: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '28px',
    fontWeight: '700',
    color: '#00d4ff',
    marginBottom: '8px',
    letterSpacing: '4px',
    textShadow: '0 0 20px rgba(0, 212, 255, 0.5)',
  },
  subtitle: {
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '12px',
    color: '#4a9eb8',
    margin: 0,
    letterSpacing: '2px',
  },
  registrationCard: {
    background: 'rgba(5, 20, 35, 0.9)',
    border: '1px solid rgba(0, 212, 255, 0.3)',
    borderRadius: '4px',
    padding: '24px',
    marginBottom: '32px',
    position: 'relative',
    zIndex: 1,
    boxShadow: '0 0 30px rgba(0, 212, 255, 0.1), inset 0 0 30px rgba(0, 212, 255, 0.02)',
  },
  corner: {
    position: 'absolute',
    width: '20px',
    height: '20px',
    border: '2px solid #00d4ff',
  },
  cornerTL: { top: -1, left: -1, borderRight: 'none', borderBottom: 'none' },
  cornerTR: { top: -1, right: -1, borderLeft: 'none', borderBottom: 'none' },
  cornerBL: { bottom: -1, left: -1, borderRight: 'none', borderTop: 'none' },
  cornerBR: { bottom: -1, right: -1, borderLeft: 'none', borderTop: 'none' },
  cardTitle: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '16px',
    fontWeight: '600',
    color: '#00d4ff',
    marginTop: 0,
    marginBottom: '8px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    letterSpacing: '2px',
  },
  icon: {
    fontSize: '18px',
  },
  cardDescription: {
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '12px',
    color: '#4a9eb8',
    marginBottom: '20px',
    lineHeight: '1.6',
    letterSpacing: '0.5px',
  },
  code: {
    background: 'rgba(0, 212, 255, 0.1)',
    padding: '2px 8px',
    borderRadius: '4px',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '12px',
    color: '#00d4ff',
    border: '1px solid rgba(0, 212, 255, 0.2)',
  },
  form: {
    marginBottom: '20px',
  },
  inputGroup: {
    display: 'flex',
    gap: '12px',
  },
  input: {
    flex: 1,
    padding: '14px 16px',
    backgroundColor: 'rgba(0, 20, 40, 0.8)',
    border: '1px solid rgba(0, 212, 255, 0.2)',
    borderRadius: '4px',
    color: '#e0f7ff',
    fontSize: '14px',
    outline: 'none',
    fontFamily: "'Share Tech Mono', monospace",
    transition: 'border-color 0.3s, box-shadow 0.3s',
  },
  registerButton: {
    padding: '14px 24px',
    background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(0, 184, 212, 0.15) 100%)',
    border: '1px solid rgba(0, 212, 255, 0.4)',
    borderRadius: '4px',
    color: '#00d4ff',
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '12px',
    fontWeight: '600',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    transition: 'all 0.3s ease',
    whiteSpace: 'nowrap',
    letterSpacing: '1px',
  },
  registerButtonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
  spinner: {
    animation: 'spin 1s linear infinite',
  },
  errorMessage: {
    marginTop: '12px',
    padding: '12px 16px',
    background: 'rgba(255, 61, 61, 0.1)',
    border: '1px solid rgba(255, 61, 61, 0.3)',
    borderRadius: '4px',
    color: '#ff3d3d',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    letterSpacing: '1px',
  },
  successMessage: {
    marginTop: '12px',
    padding: '12px 16px',
    background: 'rgba(0, 255, 136, 0.1)',
    border: '1px solid rgba(0, 255, 136, 0.3)',
    borderRadius: '4px',
    color: '#00ff88',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    letterSpacing: '1px',
  },
  tips: {
    padding: '16px',
    background: 'rgba(0, 20, 40, 0.5)',
    borderRadius: '4px',
    border: '1px solid rgba(0, 212, 255, 0.1)',
  },
  tipsTitle: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '12px',
    fontWeight: '600',
    color: '#00d4ff',
    marginTop: 0,
    marginBottom: '8px',
    letterSpacing: '1px',
  },
  tipsList: {
    margin: 0,
    paddingLeft: '20px',
    color: '#4a9eb8',
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '11px',
    lineHeight: '1.8',
    letterSpacing: '0.5px',
  },
  agentsSection: {
    background: 'rgba(5, 20, 35, 0.8)',
    border: '1px solid rgba(0, 212, 255, 0.2)',
    borderRadius: '4px',
    padding: '24px',
    position: 'relative',
    zIndex: 1,
  },
  agentsSectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  agentCount: {
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '11px',
    color: '#00d4ff',
    background: 'rgba(0, 212, 255, 0.1)',
    border: '1px solid rgba(0, 212, 255, 0.2)',
    padding: '4px 12px',
    borderRadius: '4px',
    letterSpacing: '1px',
  },
  emptyState: {
    textAlign: 'center',
    padding: '48px 24px',
  },
  emptyIcon: {
    fontSize: '48px',
    marginBottom: '16px',
  },
  emptyText: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '14px',
    color: '#4a9eb8',
    marginBottom: '8px',
    letterSpacing: '2px',
  },
  emptySubtext: {
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '12px',
    color: '#2d6880',
    letterSpacing: '0.5px',
  },
  agentsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  agentCard: {
    background: 'rgba(0, 20, 40, 0.6)',
    border: '1px solid rgba(0, 212, 255, 0.15)',
    borderRadius: '4px',
    padding: '20px',
    position: 'relative',
    transition: 'border-color 0.3s, box-shadow 0.3s',
  },
  agentHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '12px',
  },
  agentInfo: {
    flex: 1,
  },
  agentNameRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '4px',
  },
  statusIndicator: {
    fontSize: '12px',
  },
  agentName: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '14px',
    fontWeight: '600',
    color: '#e0f7ff',
    margin: 0,
    letterSpacing: '1px',
  },
  version: {
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '10px',
    color: '#4a9eb8',
    background: 'rgba(0, 212, 255, 0.1)',
    padding: '2px 8px',
    borderRadius: '4px',
    border: '1px solid rgba(0, 212, 255, 0.2)',
  },
  agentDescription: {
    fontFamily: "'Rajdhani', sans-serif",
    fontSize: '13px',
    color: '#80d4e8',
    margin: '4px 0 8px 0',
    lineHeight: '1.5',
  },
  agentUrl: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '12px',
  },
  urlLabel: {
    fontFamily: "'Share Tech Mono', monospace",
    color: '#4a9eb8',
    letterSpacing: '0.5px',
  },
  urlValue: {
    fontFamily: "'Share Tech Mono', monospace",
    color: '#00d4ff',
    fontSize: '11px',
    background: 'rgba(0, 212, 255, 0.1)',
    padding: '4px 8px',
    borderRadius: '4px',
    border: '1px solid rgba(0, 212, 255, 0.2)',
  },
  agentActions: {
    display: 'flex',
    gap: '8px',
  },
  refreshButton: {
    width: '32px',
    height: '32px',
    border: '1px solid rgba(0, 212, 255, 0.2)',
    borderRadius: '4px',
    background: 'transparent',
    color: '#00d4ff',
    fontSize: '16px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.3s ease',
  },
  deleteButton: {
    width: '32px',
    height: '32px',
    border: '1px solid rgba(255, 61, 61, 0.2)',
    borderRadius: '4px',
    background: 'transparent',
    color: '#ff3d3d',
    fontSize: '14px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.3s ease',
  },
  skillsSection: {
    marginTop: '12px',
    paddingTop: '12px',
    borderTop: '1px solid rgba(0, 212, 255, 0.1)',
  },
  skillsTitle: {
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '10px',
    fontWeight: '600',
    color: '#4a9eb8',
    marginTop: 0,
    marginBottom: '8px',
    letterSpacing: '2px',
  },
  skillsList: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '8px',
  },
  skillTag: {
    background: 'rgba(0, 212, 255, 0.1)',
    border: '1px solid rgba(0, 212, 255, 0.2)',
    borderRadius: '4px',
    padding: '8px 12px',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  skillName: {
    fontFamily: "'Rajdhani', sans-serif",
    fontSize: '12px',
    fontWeight: '500',
    color: '#00d4ff',
  },
  skillTags: {
    display: 'flex',
    gap: '4px',
  },
  tag: {
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '9px',
    color: '#4a9eb8',
    background: 'rgba(0, 20, 40, 0.8)',
    padding: '2px 6px',
    borderRadius: '4px',
    letterSpacing: '0.5px',
  },
  capabilitiesRow: {
    display: 'flex',
    gap: '12px',
    marginTop: '12px',
    paddingTop: '12px',
    borderTop: '1px solid rgba(0, 212, 255, 0.1)',
  },
  capability: {
    fontFamily: "'Share Tech Mono', monospace",
    fontSize: '11px',
    color: '#00ff88',
    background: 'rgba(0, 255, 136, 0.1)',
    border: '1px solid rgba(0, 255, 136, 0.2)',
    padding: '4px 10px',
    borderRadius: '4px',
    letterSpacing: '0.5px',
  },
  deleteConfirmOverlay: {
    position: 'absolute',
    inset: 0,
    background: 'rgba(2, 8, 16, 0.95)',
    borderRadius: '4px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backdropFilter: 'blur(4px)',
  },
  deleteConfirmBox: {
    textAlign: 'center',
    padding: '24px',
    color: '#e0f7ff',
    fontFamily: "'Rajdhani', sans-serif",
  },
  deleteConfirmActions: {
    display: 'flex',
    justifyContent: 'center',
    gap: '12px',
    marginTop: '16px',
  },
  cancelButton: {
    padding: '8px 20px',
    border: '1px solid rgba(0, 212, 255, 0.3)',
    borderRadius: '4px',
    background: 'transparent',
    color: '#00d4ff',
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '11px',
    cursor: 'pointer',
    letterSpacing: '1px',
  },
  confirmDeleteButton: {
    padding: '8px 20px',
    border: '1px solid rgba(255, 61, 61, 0.5)',
    borderRadius: '4px',
    background: 'rgba(255, 61, 61, 0.2)',
    color: '#ff3d3d',
    fontFamily: "'Orbitron', sans-serif",
    fontSize: '11px',
    fontWeight: '500',
    cursor: 'pointer',
    letterSpacing: '1px',
  },
};

// Add keyframe animation for spinner
const styleSheet = document.createElement('style');
styleSheet.textContent = `
  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
  input:focus {
    border-color: rgba(0, 212, 255, 0.5) !important;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.2), inset 0 0 10px rgba(0, 212, 255, 0.05) !important;
  }
  input::placeholder {
    color: #2d6880;
  }
  button:hover:not(:disabled) {
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.3) !important;
  }
`;
document.head.appendChild(styleSheet);

export default AdminPanel;
