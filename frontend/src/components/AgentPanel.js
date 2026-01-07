import React, { useState } from 'react';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Bot, 
  ChevronRight, 
  ChevronLeft, 
  Circle, 
  Wifi, 
  WifiOff,
  Zap
} from 'lucide-react';
import { useStore } from '../store';

const glow = keyframes`
  0%, 100% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.2); }
  50% { box-shadow: 0 0 15px rgba(0, 212, 255, 0.4); }
`;

const PanelContainer = styled(motion.aside)`
  width: ${props => props.expanded ? '300px' : '60px'};
  background: rgba(5, 16, 32, 0.95);
  border-left: 1px solid rgba(0, 212, 255, 0.2);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;
  backdrop-filter: blur(20px);
`;

const PanelHeader = styled.div`
  padding: 16px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.15);
  display: flex;
  align-items: center;
  justify-content: ${props => props.expanded ? 'space-between' : 'center'};
`;

const PanelTitle = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Orbitron', sans-serif;
  font-weight: 600;
  font-size: 0.85rem;
  white-space: nowrap;
  color: #00d4ff;
  letter-spacing: 1px;
  
  svg {
    color: #00d4ff;
    filter: drop-shadow(0 0 5px rgba(0, 212, 255, 0.5));
  }
`;

const PanelSubtitle = styled.div`
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.65rem;
  color: #4a9eb8;
  margin-top: 2px;
  letter-spacing: 0.5px;
`;

const HeaderSection = styled.div`
  display: flex;
  flex-direction: column;
`;

const ToggleButton = styled.button`
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

const AgentList = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: ${props => props.expanded ? '12px' : '12px 8px'};
`;

const AgentCard = styled(motion.div)`
  background: rgba(0, 20, 40, 0.6);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 4px;
  padding: ${props => props.expanded ? '14px' : '10px'};
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: -1px;
    left: -1px;
    width: 10px;
    height: 10px;
    border: 2px solid #00d4ff;
    border-right: none;
    border-bottom: none;
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  &:hover {
    border-color: rgba(0, 212, 255, 0.4);
    background: rgba(0, 212, 255, 0.05);
    
    &::before {
      opacity: 1;
    }
  }
`;

const AgentHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
`;

const AgentIcon = styled.div`
  width: 36px;
  height: 36px;
  border-radius: 4px;
  background: rgba(0, 20, 40, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #00d4ff;
  flex-shrink: 0;
`;

const AgentInfo = styled.div`
  flex: 1;
  min-width: 0;
  display: ${props => props.expanded ? 'block' : 'none'};
`;

const AgentName = styled.div`
  font-family: 'Rajdhani', sans-serif;
  font-weight: 500;
  font-size: 0.9rem;
  color: #e0f7ff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const AgentStatus = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.7rem;
  color: ${props => props.online ? '#00ff88' : '#4a9eb8'};
  margin-top: 4px;
  letter-spacing: 0.5px;
`;

const StatusDot = styled(Circle)`
  fill: currentColor;
  filter: ${props => props.online ? 'drop-shadow(0 0 5px rgba(0, 255, 136, 0.8))' : 'none'};
`;

const AgentDescription = styled.div`
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.8rem;
  color: #80d4e8;
  margin-top: 10px;
  line-height: 1.5;
  display: ${props => props.expanded ? 'block' : 'none'};
`;

const SkillsContainer = styled.div`
  margin-top: 10px;
  display: ${props => props.expanded ? 'flex' : 'none'};
  flex-wrap: wrap;
  gap: 6px;
`;

const SkillTag = styled.span`
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.65rem;
  padding: 3px 8px;
  background: rgba(0, 20, 40, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 4px;
  color: #4a9eb8;
`;

const ToggleContainer = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 212, 255, 0.1);
`;

const ToggleLabel = styled.span`
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.7rem;
  color: ${props => props.enabled ? '#00ff88' : '#4a9eb8'};
  font-weight: 500;
  letter-spacing: 0.5px;
`;

const ToggleSwitch = styled.button`
  background: ${props => props.enabled 
    ? 'linear-gradient(135deg, #00d4ff, #00b8d4)' 
    : 'rgba(0, 20, 40, 0.8)'};
  border: 1px solid ${props => props.enabled 
    ? 'rgba(0, 212, 255, 0.5)' 
    : 'rgba(0, 212, 255, 0.2)'};
  border-radius: 12px;
  width: 44px;
  height: 24px;
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &::after {
    content: '';
    position: absolute;
    top: 2px;
    left: ${props => props.enabled ? '22px' : '2px'};
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: ${props => props.enabled ? '#020810' : '#4a9eb8'};
    transition: all 0.3s ease;
    box-shadow: ${props => props.enabled ? '0 0 10px rgba(0, 212, 255, 0.5)' : 'none'};
  }
  
  &:hover {
    box-shadow: 0 0 15px rgba(0, 212, 255, 0.3);
  }
`;

const AgentCardWrapper = styled.div`
  position: relative;
  margin-bottom: 8px;
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
    font-size: 0.75rem;
    display: ${props => props.expanded ? 'block' : 'none'};
    letter-spacing: 1px;
  }
`;

const StatsBar = styled.div`
  padding: 12px 16px;
  border-top: 1px solid rgba(0, 212, 255, 0.15);
  display: ${props => props.expanded ? 'flex' : 'none'};
  justify-content: space-between;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.75rem;
  color: #4a9eb8;
  background: rgba(0, 20, 40, 0.5);
`;

const StatItem = styled.div`
  display: flex;
  align-items: center;
  gap: 6px;
  
  span {
    color: #00d4ff;
    font-weight: 500;
  }
`;

function AgentPanel() {
  const [expanded, setExpanded] = useState(true);
  const { agents, enabledAgents, toggleAgentEnabled } = useStore();

  const onlineAgents = agents.filter(a => a.status === 'online');
  const offlineAgents = agents.filter(a => a.status !== 'online');
  const enabledCount = agents.filter(a => enabledAgents[a.id] !== false && a.status === 'online').length;

  return (
    <PanelContainer expanded={expanded}>
      <PanelHeader expanded={expanded}>
        {expanded && (
          <HeaderSection>
            <PanelTitle>
              <Zap size={16} />
              AGENTS
            </PanelTitle>
            <PanelSubtitle>SELECT ACTIVE AGENTS</PanelSubtitle>
          </HeaderSection>
        )}
        <ToggleButton onClick={() => setExpanded(!expanded)}>
          {expanded ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </ToggleButton>
      </PanelHeader>
      
      <AgentList expanded={expanded}>
        {agents.length === 0 ? (
          <EmptyState expanded={expanded}>
            <Bot size={32} />
            <p>NO AGENTS REGISTERED</p>
          </EmptyState>
        ) : (
          <AnimatePresence>
            {[...onlineAgents, ...offlineAgents].map((agent) => {
              const isEnabled = enabledAgents[agent.id] !== false;
              const isOnline = agent.status === 'online';
              
              return (
                <AgentCardWrapper key={agent.id}>
                  <AgentCard
                    expanded={expanded}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                    style={{ opacity: isEnabled ? 1 : 0.6 }}
                  >
                    <AgentHeader>
                      <AgentIcon>
                        <Bot size={16} />
                      </AgentIcon>
                      <AgentInfo expanded={expanded}>
                        <AgentName>{agent.name}</AgentName>
                        <AgentStatus online={isOnline}>
                          {isOnline ? (
                            <>
                              <Wifi size={10} />
                              ONLINE
                            </>
                          ) : (
                            <>
                              <WifiOff size={10} />
                              OFFLINE
                            </>
                          )}
                        </AgentStatus>
                      </AgentInfo>
                    </AgentHeader>
                    
                    <AgentDescription expanded={expanded}>
                      {agent.description}
                    </AgentDescription>
                    
                    {agent.skills && agent.skills.length > 0 && (
                      <SkillsContainer expanded={expanded}>
                        {agent.skills.slice(0, 3).map((skill, idx) => (
                          <SkillTag key={idx}>{skill.name}</SkillTag>
                        ))}
                        {agent.skills.length > 3 && (
                          <SkillTag>+{agent.skills.length - 3}</SkillTag>
                        )}
                      </SkillsContainer>
                    )}
                    
                    {expanded && isOnline && (
                      <ToggleContainer>
                        <ToggleLabel enabled={isEnabled}>
                          {isEnabled ? '✓ ACTIVE' : 'INACTIVE'}
                        </ToggleLabel>
                        <ToggleSwitch 
                          enabled={isEnabled}
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleAgentEnabled(agent.id);
                          }}
                          title={isEnabled ? 'Deactivate agent' : 'Activate agent'}
                        />
                      </ToggleContainer>
                    )}
                  </AgentCard>
                </AgentCardWrapper>
              );
            })}
          </AnimatePresence>
        )}
      </AgentList>
      
      <StatsBar expanded={expanded}>
        <StatItem>
          <StatusDot size={8} online style={{ color: '#00ff88' }} />
          <span>{enabledCount}</span> ONLINE
        </StatItem>
        <StatItem>
          <StatusDot size={8} style={{ color: '#4a9eb8' }} />
          <span>{offlineAgents.length}</span> OFFLINE
        </StatItem>
      </StatsBar>
    </PanelContainer>
  );
}

export default AgentPanel;
