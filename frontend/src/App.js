import React, { useEffect } from 'react';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import AgentPanel from './components/AgentPanel';
import AdminPanel from './components/AdminPanel';
import AuthPage from './components/AuthPage';
import { useStore } from './store';

// J.A.R.V.I.S Style Animations
const glow = keyframes`
  0%, 100% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.3); }
  50% { box-shadow: 0 0 20px rgba(0, 212, 255, 0.5); }
`;

const borderPulse = keyframes`
  0%, 100% { border-color: rgba(0, 212, 255, 0.3); }
  50% { border-color: rgba(0, 212, 255, 0.6); }
`;

const AppContainer = styled.div`
  display: flex;
  height: 100vh;
  background: linear-gradient(180deg, #020810 0%, #051020 50%, #0a1828 100%);
  overflow: hidden;
  position: relative;
  
  /* Grid overlay */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      linear-gradient(rgba(0, 212, 255, 0.02) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 212, 255, 0.02) 1px, transparent 1px);
    background-size: 50px 50px;
    pointer-events: none;
    z-index: 0;
  }
`;

const AppWrapper = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  position: relative;
  z-index: 1;
`;

const TopNav = styled.nav`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  background: rgba(5, 16, 32, 0.9);
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
  backdrop-filter: blur(20px);
  z-index: 100;
  position: relative;
  
  /* HUD corners */
  &::before, &::after {
    content: '';
    position: absolute;
    width: 20px;
    height: 20px;
    border: 2px solid #00d4ff;
  }
  
  &::before {
    top: 8px;
    left: 8px;
    border-right: none;
    border-bottom: none;
  }
  
  &::after {
    top: 8px;
    right: 8px;
    border-left: none;
    border-bottom: none;
  }
`;

const LogoSection = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: scale(1.02);
    
    & > div:first-of-type {
      box-shadow: 0 0 25px rgba(0, 212, 255, 0.6);
    }
  }
`;

const LogoIcon = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0, 212, 255, 0.3) 0%, rgba(5, 20, 35, 0.9) 70%);
  border: 2px solid rgba(0, 212, 255, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: ${glow} 3s ease-in-out infinite;
  
  span {
    font-family: 'Orbitron', sans-serif;
    font-size: 18px;
    font-weight: 700;
    color: #00d4ff;
    text-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
  }
`;

const Logo = styled.div`
  font-size: 22px;
  font-weight: 700;
  font-family: 'Orbitron', sans-serif;
  color: #00d4ff;
  letter-spacing: 4px;
  text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
`;

const SystemStatus = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 16px;
  padding-left: 16px;
  border-left: 1px solid rgba(0, 212, 255, 0.2);
`;

const StatusDot = styled.div`
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00ff88;
  box-shadow: 0 0 10px rgba(0, 255, 136, 0.8);
  animation: pulse 2s ease-in-out infinite;
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }
`;

const StatusText = styled.span`
  font-family: 'Share Tech Mono', monospace;
  font-size: 10px;
  color: #00ff88;
  letter-spacing: 1px;
`;

const TabContainer = styled.div`
  display: flex;
  gap: 4px;
  background: rgba(0, 20, 40, 0.5);
  padding: 4px;
  border-radius: 4px;
  border: 1px solid rgba(0, 212, 255, 0.15);
`;

const Tab = styled.button`
  padding: 10px 24px;
  background: ${props => props.$active 
    ? 'linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(0, 184, 212, 0.15) 100%)' 
    : 'transparent'};
  border: ${props => props.$active 
    ? '1px solid rgba(0, 212, 255, 0.4)' 
    : '1px solid transparent'};
  border-radius: 4px;
  color: ${props => props.$active ? '#00d4ff' : '#4a9eb8'};
  font-size: 12px;
  font-family: 'Orbitron', sans-serif;
  font-weight: ${props => props.$active ? '600' : '500'};
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  letter-spacing: 1px;
  text-transform: uppercase;
  
  &:hover {
    background: ${props => props.$active 
      ? 'linear-gradient(135deg, rgba(0, 212, 255, 0.25) 0%, rgba(0, 184, 212, 0.2) 100%)' 
      : 'rgba(0, 212, 255, 0.1)'};
    color: #00d4ff;
    box-shadow: ${props => props.$active ? '0 0 20px rgba(0, 212, 255, 0.2)' : 'none'};
  }
`;

const TabIcon = styled.span`
  font-size: 14px;
`;

const AgentCount = styled.span`
  font-size: 10px;
  background: rgba(0, 212, 255, 0.2);
  border: 1px solid rgba(0, 212, 255, 0.3);
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 4px;
  font-family: 'Share Tech Mono', monospace;
`;

const UserSection = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

const UserAvatar = styled.div`
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0, 212, 255, 0.2) 0%, rgba(5, 20, 35, 0.8) 70%);
  border: 2px solid rgba(0, 212, 255, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #00d4ff;
  font-weight: 600;
  font-size: 14px;
  font-family: 'Orbitron', sans-serif;
  animation: ${borderPulse} 3s ease-in-out infinite;
`;

const UserName = styled.div`
  color: #e0f7ff;
  font-size: 13px;
  font-weight: 500;
  font-family: 'Rajdhani', sans-serif;
  letter-spacing: 1px;
`;

const UserRole = styled.span`
  font-family: 'Share Tech Mono', monospace;
  font-size: 10px;
  color: ${props => props.$isAdmin ? '#00ff88' : '#4a9eb8'};
  background: ${props => props.$isAdmin ? 'rgba(0, 255, 136, 0.1)' : 'rgba(0, 212, 255, 0.1)'};
  border: 1px solid ${props => props.$isAdmin ? 'rgba(0, 255, 136, 0.3)' : 'rgba(0, 212, 255, 0.2)'};
  padding: 2px 8px;
  border-radius: 4px;
  margin-left: 8px;
  letter-spacing: 1px;
`;

const LogoutButton = styled.button`
  padding: 8px 16px;
  background: rgba(255, 61, 61, 0.1);
  border: 1px solid rgba(255, 61, 61, 0.3);
  border-radius: 4px;
  color: #ff6b6b;
  font-size: 11px;
  font-family: 'Orbitron', sans-serif;
  cursor: pointer;
  transition: all 0.3s ease;
  letter-spacing: 1px;
  text-transform: uppercase;
  
  &:hover {
    background: rgba(255, 61, 61, 0.2);
    box-shadow: 0 0 15px rgba(255, 61, 61, 0.2);
  }
`;

const ContentWrapper = styled.div`
  display: flex;
  flex: 1;
  overflow: hidden;
`;

const MainContent = styled.main`
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      radial-gradient(ellipse at 20% 20%, rgba(0, 212, 255, 0.05) 0%, transparent 50%),
      radial-gradient(ellipse at 80% 80%, rgba(0, 255, 247, 0.03) 0%, transparent 50%);
    pointer-events: none;
  }
`;

const ErrorBanner = styled(motion.div)`
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 61, 61, 0.9);
  border: 1px solid rgba(255, 61, 61, 0.5);
  color: white;
  padding: 12px 24px;
  border-radius: 4px;
  z-index: 1000;
  box-shadow: 0 0 30px rgba(255, 61, 61, 0.3);
  font-family: 'Share Tech Mono', monospace;
  letter-spacing: 1px;
`;

function App() {
  const { 
    fetchConversations, 
    fetchAgents, 
    error, 
    clearError,
    sidebarOpen,
    activeTab,
    setActiveTab,
    agents,
    user,
    isAuthenticated,
    checkAuth,
    logout,
    isAdmin,
    setToken
  } = useStore();

  // Handle K-Auth callback
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const path = window.location.pathname;
    
    if (path === '/auth/callback' && token) {
      // K-Auth SSO callback - save token and redirect
      setToken(token);
      window.history.replaceState({}, '', '/');
    } else {
      checkAuth();
    }
  }, [checkAuth, setToken]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchConversations();
      fetchAgents();
      
      const interval = setInterval(fetchAgents, 30000);
      return () => clearInterval(interval);
    }
  }, [isAuthenticated, fetchConversations, fetchAgents]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(clearError, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, clearError]);

  if (!isAuthenticated) {
    return <AuthPage />;
  }

  const userIsAdmin = isAdmin();
  const userInitial = user?.name?.charAt(0)?.toUpperCase() || 'U';

  return (
    <AppContainer>
      <AppWrapper>
        <TopNav>
          <LogoSection onClick={() => setActiveTab('chat')}>
            <LogoIcon>
              <span>K</span>
            </LogoIcon>
            <Logo>K-JARVIS</Logo>
            <SystemStatus>
              <StatusDot />
              <StatusText>ONLINE</StatusText>
            </SystemStatus>
          </LogoSection>
          
          <TabContainer>
            <Tab 
              $active={activeTab === 'chat'}
              onClick={() => setActiveTab('chat')}
            >
              <TabIcon>◈</TabIcon>
              CHAT
            </Tab>
            {userIsAdmin && (
              <Tab 
                $active={activeTab === 'admin'}
                onClick={() => setActiveTab('admin')}
              >
                <TabIcon>◉</TabIcon>
                AGENTS
                {agents.length > 0 && (
                  <AgentCount>{agents.length}</AgentCount>
                )}
              </Tab>
            )}
          </TabContainer>
          
          <UserSection>
            <UserInfo>
              <UserAvatar>{userInitial}</UserAvatar>
              <UserName>
                {user?.name}
                <UserRole $isAdmin={userIsAdmin}>
                  {userIsAdmin ? 'ADMIN' : 'USER'}
                </UserRole>
              </UserName>
            </UserInfo>
            <LogoutButton onClick={logout}>
              LOGOUT
            </LogoutButton>
          </UserSection>
        </TopNav>
        
        <ContentWrapper>
          {activeTab === 'chat' || !userIsAdmin ? (
            <>
              <AnimatePresence>
                {sidebarOpen && (
                  <Sidebar />
                )}
              </AnimatePresence>
              
              <MainContent>
                <ChatArea />
              </MainContent>
              
              <AgentPanel />
            </>
          ) : (
            <AdminPanel />
          )}
        </ContentWrapper>
      </AppWrapper>
      
      <AnimatePresence>
        {error && (
          <ErrorBanner
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            ⚠ {error}
          </ErrorBanner>
        )}
      </AnimatePresence>
    </AppContainer>
  );
}

export default App;
