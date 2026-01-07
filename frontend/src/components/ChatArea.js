import React, { useRef, useEffect } from 'react';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';
import { motion, AnimatePresence } from 'framer-motion';
import { PanelLeft, Bot, Zap, MessageCircle } from 'lucide-react';
import { useStore } from '../store';
import ChatInput from './ChatInput';
import { marked } from 'marked';

const glow = keyframes`
  0%, 100% { box-shadow: 0 0 10px rgba(0, 212, 255, 0.2); }
  50% { box-shadow: 0 0 25px rgba(0, 212, 255, 0.4); }
`;

const ChatContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
  z-index: 1;
`;

const ChatHeader = styled.header`
  padding: 16px 24px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.15);
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(5, 16, 32, 0.9);
  backdrop-filter: blur(20px);
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.3), transparent);
  }
`;

const MenuButton = styled.button`
  background: none;
  border: 1px solid rgba(0, 212, 255, 0.2);
  color: #4a9eb8;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(0, 212, 255, 0.1);
    color: #00d4ff;
    border-color: rgba(0, 212, 255, 0.4);
  }
`;

const HeaderTitle = styled.h1`
  font-family: 'Orbitron', sans-serif;
  font-size: 0.9rem;
  font-weight: 500;
  color: #00d4ff;
  letter-spacing: 2px;
`;

const MessagesContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
`;

const MessageWrapper = styled(motion.div)`
  display: flex;
  gap: 16px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
`;

const Avatar = styled.div`
  width: 38px;
  height: 38px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: ${props => props.isUser 
    ? 'linear-gradient(135deg, rgba(0, 212, 255, 0.3) 0%, rgba(0, 184, 212, 0.2) 100%)' 
    : 'rgba(0, 20, 40, 0.8)'};
  border: 1px solid ${props => props.isUser ? 'rgba(0, 212, 255, 0.5)' : 'rgba(0, 212, 255, 0.2)'};
  color: #00d4ff;
  animation: ${props => props.isUser ? glow : 'none'} 3s ease-in-out infinite;
`;

const MessageContent = styled.div`
  flex: 1;
  min-width: 0;
`;

const ConversationalWrapper = styled.div`
  background: rgba(5, 20, 35, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 4px;
  padding: 16px;
  margin-bottom: 8px;
  position: relative;
  
  /* HUD corner */
  &::before {
    content: '';
    position: absolute;
    top: -1px;
    left: -1px;
    width: 15px;
    height: 15px;
    border: 2px solid #00d4ff;
    border-right: none;
    border-bottom: none;
  }
`;

const AgentGreeting = styled.div`
  font-family: 'Orbitron', sans-serif;
  font-size: 0.85rem;
  color: #00d4ff;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  letter-spacing: 1px;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
`;

const AgentResponseContent = styled.div`
  color: #e0f7ff;
  line-height: 1.8;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.95rem;
  
  p {
    margin-bottom: 12px;
    &:last-child { margin-bottom: 0; }
  }
  
  strong { 
    color: #00fff7; 
    font-weight: 600; 
  }
  
  code {
    background: rgba(0, 212, 255, 0.1);
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.85em;
    color: #00d4ff;
    border: 1px solid rgba(0, 212, 255, 0.2);
  }
  
  pre {
    background: rgba(0, 20, 40, 0.8);
    padding: 16px;
    border-radius: 4px;
    overflow-x: auto;
    margin: 12px 0;
    border: 1px solid rgba(0, 212, 255, 0.2);
    
    code {
      background: none;
      padding: 0;
      border: none;
    }
  }
  
  ul, ol {
    margin: 12px 0;
    padding-left: 24px;
  }
  
  li {
    margin-bottom: 6px;
  }
  
  a {
    color: #00d4ff;
    text-decoration: none;
    text-shadow: 0 0 5px rgba(0, 212, 255, 0.5);
    &:hover { text-decoration: underline; }
  }
  
  hr {
    border: none;
    border-top: 1px solid rgba(0, 212, 255, 0.2);
    margin: 16px 0;
  }
`;

const AgentFooter = styled.div`
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 212, 255, 0.15);
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.75rem;
  color: #4a9eb8;
  letter-spacing: 1px;
`;

const UserMessageBubble = styled.div`
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(0, 184, 212, 0.1) 100%);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 4px;
  border-bottom-right-radius: 0;
  padding: 12px 16px;
  color: #e0f7ff;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.95rem;
  line-height: 1.6;
  max-width: 80%;
  margin-left: auto;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    bottom: -1px;
    right: -1px;
    width: 10px;
    height: 10px;
    border: 2px solid #00d4ff;
    border-left: none;
    border-top: none;
  }
`;

const StreamingIndicator = styled.span`
  display: inline-block;
  width: 8px;
  height: 16px;
  background: #00d4ff;
  margin-left: 2px;
  animation: blink 1s infinite;
  border-radius: 2px;
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
  
  @keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0; }
  }
`;

const WorkflowProgressContainer = styled(motion.div)`
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
  padding: 16px;
`;

const ProgressCard = styled.div`
  background: rgba(5, 20, 35, 0.9);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 4px;
  padding: 20px;
  position: relative;
  
  &::before, &::after {
    content: '';
    position: absolute;
    width: 15px;
    height: 15px;
    border: 2px solid #00d4ff;
  }
  
  &::before {
    top: -1px;
    left: -1px;
    border-right: none;
    border-bottom: none;
  }
  
  &::after {
    bottom: -1px;
    right: -1px;
    border-left: none;
    border-top: none;
  }
`;

const ProgressHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
`;

const ProgressSpinner = styled.div`
  width: 24px;
  height: 24px;
  border: 3px solid rgba(0, 212, 255, 0.2);
  border-top: 3px solid #00d4ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  box-shadow: 0 0 15px rgba(0, 212, 255, 0.5);
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const ProgressTitle = styled.div`
  font-family: 'Orbitron', sans-serif;
  font-weight: 600;
  color: #00d4ff;
  font-size: 0.9rem;
  letter-spacing: 1px;
`;

const ProgressStatus = styled.div`
  font-family: 'Share Tech Mono', monospace;
  color: #80d4e8;
  font-size: 0.85rem;
  margin-bottom: 12px;
`;

const ProgressBarContainer = styled.div`
  height: 6px;
  background: rgba(0, 212, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
  border: 1px solid rgba(0, 212, 255, 0.2);
`;

const ProgressBarFill = styled(motion.div)`
  height: 100%;
  background: linear-gradient(90deg, #00d4ff, #00fff7);
  border-radius: 3px;
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
`;

const ProgressSteps = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.75rem;
  color: #4a9eb8;
`;

const ProgressStep = styled.span`
  padding: 4px 10px;
  background: ${props => props.$active 
    ? 'rgba(0, 212, 255, 0.2)' 
    : 'rgba(0, 20, 40, 0.5)'};
  border: 1px solid ${props => props.$active 
    ? 'rgba(0, 212, 255, 0.4)' 
    : 'rgba(0, 212, 255, 0.1)'};
  border-radius: 4px;
  color: ${props => props.$active ? '#00d4ff' : 'inherit'};
`;

const ElapsedTime = styled.span`
  margin-left: auto;
  font-size: 0.7rem;
  color: #4a9eb8;
`;

// Arc Reactor Style Animations
const rotateOuter = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const rotateInner = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(-360deg); }
`;

const pulseCore = keyframes`
  0%, 100% { 
    box-shadow: 0 0 30px rgba(0, 212, 255, 0.6), 
                0 0 60px rgba(0, 212, 255, 0.4),
                0 0 90px rgba(0, 212, 255, 0.2),
                inset 0 0 30px rgba(0, 212, 255, 0.3);
  }
  50% { 
    box-shadow: 0 0 50px rgba(0, 212, 255, 0.8), 
                0 0 100px rgba(0, 212, 255, 0.5),
                0 0 150px rgba(0, 212, 255, 0.3),
                inset 0 0 50px rgba(0, 212, 255, 0.5);
  }
`;

const WelcomeContainer = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
  position: relative;
  overflow: hidden;
  
  /* Background grid effect */
  &::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 800px;
    height: 800px;
    background: 
      radial-gradient(circle, rgba(0, 212, 255, 0.1) 0%, transparent 60%);
    pointer-events: none;
  }
`;

const ArcReactorContainer = styled(motion.div)`
  position: relative;
  width: 320px;
  height: 320px;
  margin-bottom: 40px;
  cursor: pointer;
  
  &:hover {
    .arc-core {
      animation: ${pulseCore} 1s ease-in-out infinite;
    }
    .start-text {
      color: #00fff7;
      text-shadow: 0 0 30px rgba(0, 255, 247, 0.8);
    }
  }
`;

const OuterRing = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 2px solid rgba(0, 212, 255, 0.3);
  border-radius: 50%;
  animation: ${rotateOuter} 30s linear infinite;
  
  /* Tick marks */
  &::before {
    content: '';
    position: absolute;
    top: -10px;
    left: 50%;
    transform: translateX(-50%);
    width: 2px;
    height: 20px;
    background: #00d4ff;
    box-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
  }
  
  /* Additional tick marks using box-shadow */
  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 100%;
    height: 100%;
    transform: translate(-50%, -50%);
    border: 1px dashed rgba(0, 212, 255, 0.2);
    border-radius: 50%;
  }
`;

const MiddleRing = styled.div`
  position: absolute;
  top: 30px;
  left: 30px;
  width: calc(100% - 60px);
  height: calc(100% - 60px);
  border: 3px solid rgba(0, 212, 255, 0.4);
  border-radius: 50%;
  animation: ${rotateInner} 20s linear infinite;
  
  /* Segments */
  background: 
    conic-gradient(
      from 0deg,
      transparent 0deg 30deg,
      rgba(0, 212, 255, 0.1) 30deg 60deg,
      transparent 60deg 90deg,
      rgba(0, 212, 255, 0.1) 90deg 120deg,
      transparent 120deg 150deg,
      rgba(0, 212, 255, 0.1) 150deg 180deg,
      transparent 180deg 210deg,
      rgba(0, 212, 255, 0.1) 210deg 240deg,
      transparent 240deg 270deg,
      rgba(0, 212, 255, 0.1) 270deg 300deg,
      transparent 300deg 330deg,
      rgba(0, 212, 255, 0.1) 330deg 360deg
    );
`;

const InnerRing = styled.div`
  position: absolute;
  top: 60px;
  left: 60px;
  width: calc(100% - 120px);
  height: calc(100% - 120px);
  border: 2px solid rgba(0, 212, 255, 0.5);
  border-radius: 50%;
  animation: ${rotateOuter} 15s linear infinite;
  
  /* Inner glow */
  &::before {
    content: '';
    position: absolute;
    top: 10px;
    left: 10px;
    right: 10px;
    bottom: 10px;
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 50%;
  }
`;

const ArcCore = styled.div`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 140px;
  height: 140px;
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(0, 255, 247, 0.9) 0%,
    rgba(0, 212, 255, 0.7) 30%,
    rgba(0, 184, 212, 0.4) 60%,
    rgba(5, 20, 35, 0.9) 100%
  );
  border: 3px solid rgba(0, 212, 255, 0.8);
  animation: ${pulseCore} 3s ease-in-out infinite;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
`;

const TriangleIcon = styled.div`
  width: 0;
  height: 0;
  border-left: 20px solid transparent;
  border-right: 20px solid transparent;
  border-bottom: 35px solid rgba(255, 255, 255, 0.9);
  filter: drop-shadow(0 0 10px rgba(0, 212, 255, 0.8));
  margin-bottom: 8px;
`;

const StartText = styled.div`
  font-family: 'Orbitron', sans-serif;
  font-size: 11px;
  font-weight: 700;
  color: #e0f7ff;
  letter-spacing: 2px;
  text-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
  transition: all 0.3s ease;
`;

const StatusRing = styled.div`
  position: absolute;
  top: 90px;
  left: 90px;
  width: calc(100% - 180px);
  height: calc(100% - 180px);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
`;

const DataPoint = styled.div`
  position: absolute;
  width: 8px;
  height: 8px;
  background: #00d4ff;
  border-radius: 50%;
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.8);
  
  &:nth-of-type(1) { top: 0; left: 50%; transform: translateX(-50%); }
  &:nth-of-type(2) { top: 50%; right: 0; transform: translateY(-50%); }
  &:nth-of-type(3) { bottom: 0; left: 50%; transform: translateX(-50%); }
  &:nth-of-type(4) { top: 50%; left: 0; transform: translateY(-50%); }
`;

const WelcomeTitle = styled.h2`
  font-family: 'Orbitron', sans-serif;
  font-size: 1.8rem;
  font-weight: 700;
  margin-bottom: 16px;
  color: #00d4ff;
  letter-spacing: 4px;
  text-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
`;

const WelcomeSubtitle = styled.p`
  font-family: 'Rajdhani', sans-serif;
  color: #80d4e8;
  max-width: 500px;
  margin-bottom: 20px;
  line-height: 1.8;
  font-size: 1.1rem;
`;

const IntelligenceDisplay = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 30px;
  padding: 24px 50px;
  background: rgba(5, 20, 35, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 12px;
  position: relative;
  
  &::before, &::after {
    content: '';
    position: absolute;
    width: 15px;
    height: 15px;
    border: 2px solid #00d4ff;
  }
  
  &::before {
    top: -1px;
    left: -1px;
    border-right: none;
    border-bottom: none;
  }
  
  &::after {
    bottom: -1px;
    right: -1px;
    border-left: none;
    border-top: none;
  }
`;

const IntelligenceLabel = styled.span`
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.85rem;
  color: #4a9eb8;
  letter-spacing: 2px;
  text-transform: uppercase;
`;

const IntelligenceRow = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: nowrap;
  white-space: nowrap;
`;

const IntelligenceText = styled.span`
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.2rem;
  color: #80d4e8;
  letter-spacing: 1px;
`;

const IntelligenceValue = styled.span`
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 2.5rem;
  font-weight: 700;
  color: ${props => props.$value > 0 ? '#00ff88' : '#00d4ff'};
  text-shadow: 0 0 30px ${props => props.$value > 0 ? 'rgba(0, 255, 136, 0.6)' : 'rgba(0, 212, 255, 0.6)'};
  line-height: 1;
  padding: 4px 16px;
  background: rgba(0, 20, 40, 0.6);
  border-radius: 8px;
  border: 2px solid ${props => props.$value > 0 ? 'rgba(0, 255, 136, 0.4)' : 'rgba(0, 212, 255, 0.4)'};
  min-width: 50px;
  text-align: center;
`;

const IntelligenceUnit = styled.span`
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.8rem;
  color: #4a9eb8;
  letter-spacing: 1px;
  margin-top: 4px;
`;

const IQLevelBadge = styled.div`
  font-family: 'Orbitron', sans-serif;
  font-size: 0.9rem;
  font-weight: 600;
  color: ${props => props.$color || '#00d4ff'};
  letter-spacing: 2px;
  padding: 6px 16px;
  background: rgba(0, 20, 40, 0.6);
  border: 1px solid ${props => props.$color || '#00d4ff'}40;
  border-radius: 20px;
  margin-top: 8px;
  text-shadow: 0 0 15px ${props => props.$color || '#00d4ff'}80;
  animation: ${props => props.$iq > 300 ? 'pulse 2s infinite' : 'none'};
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
`;

// Removed unused components

function ChatArea() {
  const { 
    messages, 
    isLoading, 
    sidebarOpen, 
    setSidebarOpen,
    sendMessage,
    workflowProgress,
    agents
  } = useStore();
  
  // IQ 계산: 기본 100 + 스킬당 15
  const calculateIQ = () => {
    const onlineAgentsList = agents.filter(a => a.status === 'online');
    if (onlineAgentsList.length === 0) return 0;
    
    let totalIQ = 0;
    onlineAgentsList.forEach(agent => {
      const baseIQ = 100; // 에이전트당 기본 IQ
      const skillCount = agent.skills?.length || 0;
      const skillBonus = skillCount * 15; // 스킬당 +15 IQ
      totalIQ += baseIQ + skillBonus;
    });
    
    return totalIQ;
  };
  
  const jarvisIQ = calculateIQ();
  const onlineAgents = agents.filter(a => a.status === 'online').length;
  
  // IQ 레벨 텍스트
  const getIQLevel = (iq) => {
    if (iq === 0) return { text: 'STANDBY MODE', color: '#4a9eb8' };
    if (iq <= 150) return { text: 'HUMAN LEVEL', color: '#00d4ff' };
    if (iq <= 350) return { text: 'ADVANCED', color: '#00e5cc' };
    if (iq <= 600) return { text: 'GENIUS LEVEL', color: '#00ff88' };
    if (iq <= 1000) return { text: 'SUPERHUMAN', color: '#ffaa00' };
    if (iq <= 2000) return { text: 'LEGENDARY', color: '#ff6600' };
    return { text: 'GODLIKE', color: '#ff00ff' };
  };
  
  const iqLevel = getIQLevel(jarvisIQ);
  
  const messagesEndRef = useRef(null);
  
  const getElapsedTime = () => {
    if (!workflowProgress.startTime) return '';
    const elapsed = Math.floor((Date.now() - workflowProgress.startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    return minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
  };
  
  useEffect(() => {
    if (workflowProgress.isActive) {
      const interval = setInterval(() => {
        setSidebarOpen(sidebarOpen);
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [workflowProgress.isActive, setSidebarOpen, sidebarOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const renderMessage = (message) => {
    const isUser = message.role === 'user';
    const html = marked.parse(message.content || '');
    const agentName = message.metadata?.agent;
    
    if (isUser) {
      return (
        <MessageWrapper
          key={message.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          style={{ justifyContent: 'flex-end' }}
        >
          <UserMessageBubble>
            {message.content}
          </UserMessageBubble>
        </MessageWrapper>
      );
    }
    
    return (
      <MessageWrapper
        key={message.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <Avatar isUser={false}>
          <Bot size={18} />
        </Avatar>
        <MessageContent>
          <ConversationalWrapper>
            {agentName && (
              <AgentGreeting>
                <MessageCircle size={14} />
                {agentName.toUpperCase()} RESPONSE
              </AgentGreeting>
            )}
            <AgentResponseContent>
              <div dangerouslySetInnerHTML={{ __html: html }} />
              {message.metadata?.streaming && <StreamingIndicator />}
            </AgentResponseContent>
            {agentName && !message.metadata?.streaming && (
              <AgentFooter>
                <Zap size={12} />
                PROCESSED BY {agentName.toUpperCase()}
              </AgentFooter>
            )}
          </ConversationalWrapper>
        </MessageContent>
      </MessageWrapper>
    );
  };

  return (
    <ChatContainer>
      <ChatHeader>
        {!sidebarOpen && (
          <MenuButton onClick={() => setSidebarOpen(true)}>
            <PanelLeft size={20} />
          </MenuButton>
        )}
        <HeaderTitle>AI ASSISTANT</HeaderTitle>
      </ChatHeader>
      
      {messages.length === 0 ? (
        <WelcomeContainer>
          <ArcReactorContainer
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: 'spring', duration: 0.8 }}
            whileHover={{ scale: 1.02 }}
          >
            <OuterRing />
            <MiddleRing />
            <InnerRing />
            <StatusRing>
              <DataPoint />
              <DataPoint />
              <DataPoint />
              <DataPoint />
            </StatusRing>
            <ArcCore className="arc-core">
              <TriangleIcon />
              <StartText className="start-text">READY</StartText>
            </ArcCore>
          </ArcReactorContainer>
          
          <WelcomeTitle>K-JARVIS ONLINE</WelcomeTitle>
          <WelcomeSubtitle>
            무엇이든 물어보세요. AI가 최적의 에이전트를 선택합니다.
          </WelcomeSubtitle>
          
          <IntelligenceDisplay>
            <IntelligenceLabel>INTELLIGENCE QUOTIENT</IntelligenceLabel>
            <IntelligenceRow>
              <IntelligenceText>K-JARVIS IQ</IntelligenceText>
              <IntelligenceValue $value={jarvisIQ}>
                {jarvisIQ}
              </IntelligenceValue>
            </IntelligenceRow>
            <IQLevelBadge $color={iqLevel.color} $iq={jarvisIQ}>
              {iqLevel.text}
            </IQLevelBadge>
            <IntelligenceUnit>
              {onlineAgents > 0 
                ? `${onlineAgents} AGENTS · ${agents.filter(a => a.status === 'online').reduce((sum, a) => sum + (a.skills?.length || 0), 0)} SKILLS`
                : 'AWAITING AGENT CONNECTION'}
            </IntelligenceUnit>
          </IntelligenceDisplay>
        </WelcomeContainer>
      ) : (
        <MessagesContainer>
          <AnimatePresence>
            {messages.map(renderMessage)}
          </AnimatePresence>
          
          {workflowProgress.isActive && (
            <WorkflowProgressContainer
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <ProgressCard>
                <ProgressHeader>
                  <ProgressSpinner />
                  <ProgressTitle>PROCESSING REQUEST</ProgressTitle>
                </ProgressHeader>
                <ProgressStatus>{workflowProgress.statusMessage}</ProgressStatus>
                <ProgressBarContainer>
                  <ProgressBarFill
                    initial={{ width: '0%' }}
                    animate={{ 
                      width: `${(workflowProgress.currentStep / workflowProgress.totalSteps) * 100}%` 
                    }}
                    transition={{ duration: 0.5 }}
                  />
                </ProgressBarContainer>
                <ProgressSteps>
                  {workflowProgress.totalSteps > 1 ? (
                    <>
                      <ProgressStep $active={workflowProgress.currentStep >= 1}>
                        STEP 1: DATA
                      </ProgressStep>
                      <span>→</span>
                      <ProgressStep $active={workflowProgress.currentStep >= 2}>
                        STEP 2: PROCESS
                      </ProgressStep>
                    </>
                  ) : (
                    <ProgressStep $active={true}>PROCESSING</ProgressStep>
                  )}
                  <ElapsedTime>{getElapsedTime()}</ElapsedTime>
                </ProgressSteps>
              </ProgressCard>
            </WorkflowProgressContainer>
          )}
          
          <div ref={messagesEndRef} />
        </MessagesContainer>
      )}
      
      <ChatInput />
    </ChatContainer>
  );
}

export default ChatArea;
