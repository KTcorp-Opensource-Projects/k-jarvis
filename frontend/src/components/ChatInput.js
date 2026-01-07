import React, { useState, useRef, useEffect } from 'react';
import styled from '@emotion/styled';
import { keyframes } from '@emotion/react';
import { motion } from 'framer-motion';
import { Send, Zap } from 'lucide-react';
import { useStore } from '../store';

const glow = keyframes`
  0%, 100% { box-shadow: 0 0 5px rgba(0, 212, 255, 0.3); }
  50% { box-shadow: 0 0 15px rgba(0, 212, 255, 0.5); }
`;

const InputContainer = styled.div`
  padding: 16px 24px 24px;
  background: linear-gradient(to top, rgba(2, 8, 16, 0.95) 0%, transparent 100%);
`;

const InputWrapper = styled.div`
  max-width: 900px;
  margin: 0 auto;
  position: relative;
`;

const TextAreaContainer = styled.div`
  background: rgba(5, 20, 35, 0.9);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 4px;
  transition: all 0.3s ease;
  position: relative;
  
  /* HUD corners */
  &::before, &::after {
    content: '';
    position: absolute;
    width: 12px;
    height: 12px;
    border: 2px solid #00d4ff;
    pointer-events: none;
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
  
  &:focus-within {
    border-color: rgba(0, 212, 255, 0.5);
    box-shadow: 0 0 30px rgba(0, 212, 255, 0.2), inset 0 0 20px rgba(0, 212, 255, 0.05);
  }
`;

const TextArea = styled.textarea`
  width: 100%;
  min-height: 56px;
  max-height: 200px;
  padding: 16px 60px 16px 20px;
  background: transparent;
  border: none;
  color: #e0f7ff;
  font-family: 'Rajdhani', sans-serif;
  font-size: 1rem;
  line-height: 1.5;
  resize: none;
  outline: none;
  
  &::placeholder {
    color: #2d6880;
    font-family: 'Share Tech Mono', monospace;
  }
`;

const SendButton = styled(motion.button)`
  position: absolute;
  right: 12px;
  bottom: 12px;
  width: 40px;
  height: 40px;
  border-radius: 4px;
  border: 1px solid ${props => props.disabled 
    ? 'rgba(0, 212, 255, 0.1)' 
    : 'rgba(0, 212, 255, 0.5)'};
  background: ${props => props.disabled 
    ? 'rgba(0, 20, 40, 0.5)' 
    : 'linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(0, 184, 212, 0.15) 100%)'};
  color: ${props => props.disabled ? '#2d6880' : '#00d4ff'};
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  
  &:not(:disabled):hover {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.3) 0%, rgba(0, 184, 212, 0.25) 100%);
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.4);
    animation: ${glow} 2s ease-in-out infinite;
  }
`;

const HintText = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.75rem;
  color: #4a9eb8;
  letter-spacing: 1px;
  
  svg {
    color: #00d4ff;
  }
  
  kbd {
    background: rgba(0, 20, 40, 0.8);
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.7rem;
    border: 1px solid rgba(0, 212, 255, 0.2);
    color: #00d4ff;
  }
`;

const Divider = styled.span`
  color: rgba(0, 212, 255, 0.3);
`;

const LoadingDots = styled.div`
  display: flex;
  gap: 4px;
  
  span {
    width: 6px;
    height: 6px;
    background: #00d4ff;
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;
    box-shadow: 0 0 8px rgba(0, 212, 255, 0.8);
    
    &:nth-of-type(1) { animation-delay: -0.32s; }
    &:nth-of-type(2) { animation-delay: -0.16s; }
    &:nth-of-type(3) { animation-delay: 0s; }
  }
  
  @keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  }
`;

function ChatInput() {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);
  const { sendMessage, isLoading, isStreaming } = useStore();

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    
    if (!input.trim() || isLoading || isStreaming) return;
    
    sendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isDisabled = !input.trim() || isLoading || isStreaming;

  return (
    <InputContainer>
      <InputWrapper>
        <TextAreaContainer>
          <TextArea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="ENTER YOUR MESSAGE..."
            disabled={isLoading || isStreaming}
            rows={1}
          />
          <SendButton
            type="button"
            disabled={isDisabled}
            onClick={handleSubmit}
            whileTap={{ scale: 0.95 }}
          >
            {isLoading || isStreaming ? (
              <LoadingDots>
                <span />
                <span />
                <span />
              </LoadingDots>
            ) : (
              <Send size={18} />
            )}
          </SendButton>
        </TextAreaContainer>
        
        <HintText>
          <Zap size={12} />
          AI ROUTES TO OPTIMAL AGENT
          <Divider>|</Divider>
          <kbd>ENTER</kbd> SEND
          <kbd>SHIFT+ENTER</kbd> NEWLINE
        </HintText>
      </InputWrapper>
    </InputContainer>
  );
}

export default ChatInput;
