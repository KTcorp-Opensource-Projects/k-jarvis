import React from 'react';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';
import { motion } from 'framer-motion';
import { 
  MessageSquarePlus, 
  MessageCircle, 
  Trash2, 
  PanelLeftClose,
  Zap
} from 'lucide-react';
import { useStore } from '../store';

const borderGlow = keyframes`
  0%, 100% { border-color: rgba(0, 212, 255, 0.2); }
  50% { border-color: rgba(0, 212, 255, 0.4); }
`;

const SidebarContainer = styled(motion.aside)`
  width: 280px;
  background: rgba(5, 16, 32, 0.95);
  border-right: 1px solid rgba(0, 212, 255, 0.2);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  backdrop-filter: blur(20px);
`;

const SidebarHeader = styled.div`
  padding: 20px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Orbitron', sans-serif;
  font-weight: 600;
  font-size: 0.9rem;
  color: #00d4ff;
  letter-spacing: 1px;
  
  svg {
    color: #00d4ff;
    filter: drop-shadow(0 0 5px rgba(0, 212, 255, 0.5));
  }
`;

const CloseButton = styled.button`
  background: none;
  border: 1px solid rgba(0, 212, 255, 0.2);
  color: #4a9eb8;
  cursor: pointer;
  padding: 6px;
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

const NewChatButton = styled.button`
  margin: 16px;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(0, 184, 212, 0.15) 100%);
  border: 1px solid rgba(0, 212, 255, 0.4);
  border-radius: 4px;
  color: #00d4ff;
  font-family: 'Orbitron', sans-serif;
  font-weight: 500;
  font-size: 12px;
  letter-spacing: 1px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
  text-transform: uppercase;
  
  &:hover {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.3) 0%, rgba(0, 184, 212, 0.25) 100%);
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
    transform: translateY(-1px);
  }
  
  &:active {
    transform: translateY(0);
  }
`;

const ConversationList = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 8px;
`;

const ConversationItem = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: ${props => props.active ? 'rgba(0, 212, 255, 0.1)' : 'transparent'};
  border: 1px solid ${props => props.active ? 'rgba(0, 212, 255, 0.3)' : 'transparent'};
  margin-bottom: 4px;
  animation: ${props => props.active ? borderGlow : 'none'} 3s ease-in-out infinite;
  
  &:hover {
    background: rgba(0, 212, 255, 0.08);
    border-color: rgba(0, 212, 255, 0.2);
  }
  
  &:hover button {
    opacity: 1;
  }
`;

const ConversationIcon = styled.div`
  width: 32px;
  height: 32px;
  border-radius: 4px;
  background: rgba(0, 20, 40, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #00d4ff;
  flex-shrink: 0;
`;

const ConversationInfo = styled.div`
  flex: 1;
  min-width: 0;
`;

const ConversationTitle = styled.div`
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.9rem;
  color: #e0f7ff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const ConversationDate = styled.div`
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.7rem;
  color: #4a9eb8;
  margin-top: 2px;
`;

const DeleteButton = styled.button`
  background: none;
  border: none;
  color: #4a9eb8;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  opacity: 0;
  transition: all 0.3s ease;
  
  &:hover {
    color: #ff3d3d;
    background: rgba(255, 61, 61, 0.1);
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 40px 20px;
  color: #4a9eb8;
  
  svg {
    margin-bottom: 12px;
    opacity: 0.5;
    color: #00d4ff;
  }
  
  p {
    font-family: 'Share Tech Mono', monospace;
    font-size: 12px;
    letter-spacing: 1px;
  }
`;

function Sidebar() {
  const { 
    conversations, 
    currentConversationId, 
    createConversation, 
    selectConversation,
    deleteConversation,
    setSidebarOpen
  } = useStore();

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 86400000) {
      return '오늘';
    } else if (diff < 172800000) {
      return '어제';
    } else {
      return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' });
    }
  };

  return (
    <SidebarContainer
      initial={{ width: 0, opacity: 0 }}
      animate={{ width: 280, opacity: 1 }}
      exit={{ width: 0, opacity: 0 }}
      transition={{ duration: 0.2 }}
    >
      <SidebarHeader>
        <Logo>
          <Zap size={18} />
          CONVERSATIONS
        </Logo>
        <CloseButton onClick={() => setSidebarOpen(false)}>
          <PanelLeftClose size={18} />
        </CloseButton>
      </SidebarHeader>
      
      <NewChatButton onClick={createConversation}>
        <MessageSquarePlus size={16} />
        NEW CHAT
      </NewChatButton>
      
      <ConversationList>
        {conversations.length === 0 ? (
          <EmptyState>
            <MessageCircle size={32} />
            <p>NO CONVERSATIONS</p>
          </EmptyState>
        ) : (
          conversations.map((conv) => (
            <ConversationItem
              key={conv.id}
              active={conv.id === currentConversationId}
              onClick={() => selectConversation(conv.id)}
            >
              <ConversationIcon>
                <MessageCircle size={14} />
              </ConversationIcon>
              <ConversationInfo>
                <ConversationTitle>{conv.title}</ConversationTitle>
                <ConversationDate>{formatDate(conv.updated_at)}</ConversationDate>
              </ConversationInfo>
              <DeleteButton 
                onClick={(e) => {
                  e.stopPropagation();
                  deleteConversation(conv.id);
                }}
              >
                <Trash2 size={14} />
              </DeleteButton>
            </ConversationItem>
          ))
        )}
      </ConversationList>
    </SidebarContainer>
  );
}

export default Sidebar;
