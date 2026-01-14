import React, { useState, useEffect } from 'react';
import styled from '@emotion/styled';
import { motion, AnimatePresence } from 'framer-motion';
import { useStore } from '../store';
import { Key, Plus, Trash2, X, Shield, Clock, Check, AlertTriangle } from 'lucide-react';

const Overlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 5, 10, 0.85);
  backdrop-filter: blur(5px);
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
`;

const ModalContainer = styled(motion.div)`
  background: rgba(5, 16, 32, 0.95);
  border: 1px solid rgba(0, 212, 255, 0.3);
  border-radius: 8px;
  width: 90%;
  max-width: 600px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 0 50px rgba(0, 212, 255, 0.2);
  position: relative;
  overflow: hidden;

  /* Grid overlay */
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      linear-gradient(rgba(0, 212, 255, 0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0, 212, 255, 0.03) 1px, transparent 1px);
    background-size: 30px 30px;
    pointer-events: none;
  }
`;

const Header = styled.div`
  padding: 20px 24px;
  border-bottom: 1px solid rgba(0, 212, 255, 0.2);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(0, 20, 40, 0.5);
`;

const Title = styled.h2`
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  color: #00d4ff;
  font-family: 'Orbitron', sans-serif;
  font-size: 1.2rem;
  letter-spacing: 1px;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  color: #4a9eb8;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  transition: all 0.2s;

  &:hover {
    color: #00d4ff;
    background: rgba(0, 212, 255, 0.1);
  }
`;

const Content = styled.div`
  padding: 24px;
  overflow-y: auto;
  flex: 1;
`;

const Section = styled.div`
  margin-bottom: 24px;
`;

const SectionTitle = styled.h3`
  font-family: 'Share Tech Mono', monospace;
  color: #4a9eb8;
  font-size: 0.9rem;
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;

  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(0, 212, 255, 0.1);
  }
`;

const TokenList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const TokenItem = styled.div`
  background: rgba(0, 212, 255, 0.05);
  border: 1px solid rgba(0, 212, 255, 0.1);
  border-radius: 4px;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s;

  &:hover {
    border-color: rgba(0, 212, 255, 0.3);
    background: rgba(0, 212, 255, 0.08);
  }
`;

const TokenInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
`;

const TokenName = styled.div`
  color: #e0f7ff;
  font-family: 'Rajdhani', sans-serif;
  font-weight: 600;
  font-size: 1rem;
`;

const TokenMeta = styled.div`
  display: flex;
  gap: 12px;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.75rem;
  color: #4a9eb8;
`;

const StatusBadge = styled.span`
  color: ${props => props.active ? '#00ff88' : '#ff3d3d'};
  display: flex;
  align-items: center;
  gap: 4px;
`;

const DeleteBtn = styled.button`
  background: rgba(255, 61, 61, 0.1);
  color: #ff3d3d;
  border: 1px solid rgba(255, 61, 61, 0.2);
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: rgba(255, 61, 61, 0.2);
    border-color: rgba(255, 61, 61, 0.4);
  }
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: rgba(0, 20, 40, 0.3);
  padding: 20px;
  border-radius: 4px;
  border: 1px solid rgba(0, 212, 255, 0.1);
`;

const InputGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const Label = styled.label`
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.8rem;
  color: #4a9eb8;
`;

const Input = styled.input`
  background: rgba(5, 16, 32, 0.8);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 4px;
  padding: 10px 12px;
  color: #e0f7ff;
  font-family: 'Rajdhani', sans-serif;
  outline: none;
  transition: all 0.2s;

  &:focus {
    border-color: #00d4ff;
    box-shadow: 0 0 10px rgba(0, 212, 255, 0.1);
  }
`;

const SubmitButton = styled.button`
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(0, 184, 212, 0.15) 100%);
  border: 1px solid rgba(0, 212, 255, 0.4);
  color: #00d4ff;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: 8px;

  &:hover:not(:disabled) {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.3) 0%, rgba(0, 184, 212, 0.25) 100%);
    box-shadow: 0 0 15px rgba(0, 212, 255, 0.2);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 30px;
  color: #4a9eb8;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.9rem;
  border: 1px dashed rgba(0, 212, 255, 0.2);
  border-radius: 4px;
`;

const ErrorMessage = styled.div`
  color: #ff3d3d;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.8rem;
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
`;

const HelpText = styled.div`
  font-size: 0.75rem;
  color: #4a9eb8;
  margin-top: 4px;
  opacity: 0.7;
`;

export default function KeyManagementModal() {
    const {
        isKeyModalOpen,
        setKeyModalOpen,
        mcpTokens,
        fetchMcpTokens,
        registerMcpToken,
        deleteMcpToken,
        isKeyOperationLoading,
        keyModalError
    } = useStore();

    const [newToken, setNewToken] = useState('');
    const [tokenName, setTokenName] = useState('');
    const [expiry, setExpiry] = useState('');

    useEffect(() => {
        if (isKeyModalOpen) {
            fetchMcpTokens();
            setNewToken('');
            setTokenName('');
            setExpiry('');
        }
    }, [isKeyModalOpen, fetchMcpTokens]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!newToken || !tokenName) return;

        const result = await registerMcpToken(newToken, tokenName, expiry);
        if (result.success) {
            setNewToken('');
            setTokenName('');
            setExpiry('');
        }
    };

    if (!isKeyModalOpen) return null;

    return (
        <AnimatePresence>
            <Overlay
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setKeyModalOpen(false)}
            >
                <ModalContainer
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.9, opacity: 0 }}
                    onClick={e => e.stopPropagation()}
                >
                    <Header>
                        <Title>
                            <Key size={20} />
                            KEY MANAGEMENT
                        </Title>
                        <CloseButton onClick={() => setKeyModalOpen(false)}>
                            <X size={20} />
                        </CloseButton>
                    </Header>

                    <Content>
                        <Section>
                            <SectionTitle>
                                <Plus size={16} /> ADD NEW TOKEN
                            </SectionTitle>
                            <Form onSubmit={handleSubmit}>
                                <InputGroup>
                                    <Label>TOKEN NAME (Unique Identifier)</Label>
                                    <Input
                                        placeholder="e.g., github-pat-work"
                                        value={tokenName}
                                        onChange={e => setTokenName(e.target.value)}
                                        disabled={isKeyOperationLoading}
                                    />
                                </InputGroup>

                                <InputGroup>
                                    <Label>TOKEN VALUE (Encrypted Storage)</Label>
                                    <Input
                                        type="password"
                                        placeholder="ghp_xxxxxxxxxxxx"
                                        value={newToken}
                                        onChange={e => setNewToken(e.target.value)}
                                        disabled={isKeyOperationLoading}
                                    />
                                    <HelpText>Tokens are encrypted using AES-256-GCM before storage.</HelpText>
                                </InputGroup>

                                <InputGroup>
                                    <Label>EXPIRY (Days, Optional)</Label>
                                    <Input
                                        type="number"
                                        placeholder="30"
                                        value={expiry}
                                        onChange={e => setExpiry(e.target.value)}
                                        disabled={isKeyOperationLoading}
                                    />
                                </InputGroup>

                                {keyModalError && (
                                    <ErrorMessage>
                                        <AlertTriangle size={14} /> {keyModalError}
                                    </ErrorMessage>
                                )}

                                <SubmitButton type="submit" disabled={isKeyOperationLoading || !newToken || !tokenName}>
                                    {isKeyOperationLoading ? 'PROCESSING...' : 'SECURE SAVE'}
                                </SubmitButton>
                            </Form>
                        </Section>

                        <Section>
                            <SectionTitle>
                                <Shield size={16} /> YOUR VAULT
                            </SectionTitle>

                            <TokenList>
                                {mcpTokens.length === 0 ? (
                                    <EmptyState>NO TOKENS STORED</EmptyState>
                                ) : (
                                    mcpTokens.map((token) => (
                                        <TokenItem key={token.token_name}>
                                            <TokenInfo>
                                                <TokenName>{token.token_name}</TokenName>
                                                <TokenMeta>
                                                    <StatusBadge active={!token.is_expired}>
                                                        {token.is_expired ? 'EXPIRED' : 'ACTIVE'} <Check size={12} />
                                                    </StatusBadge>
                                                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                                        <Clock size={12} />
                                                        {token.expires_at ? new Date(token.expires_at).toLocaleDateString() : 'Never'}
                                                    </span>
                                                </TokenMeta>
                                            </TokenInfo>
                                            <DeleteBtn
                                                onClick={() => deleteMcpToken(token.token_name)}
                                                disabled={isKeyOperationLoading}
                                                title="Delete Token"
                                            >
                                                <Trash2 size={16} />
                                            </DeleteBtn>
                                        </TokenItem>
                                    ))
                                )}
                            </TokenList>
                        </Section>
                    </Content>
                </ModalContainer>
            </Overlay>
        </AnimatePresence>
    );
}
