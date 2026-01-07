import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:4001';

// Helper to get auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

export const useStore = create(
  persist(
    (set, get) => ({
      // Auth State
      user: null,
      isAuthenticated: false,
      authLoading: false,
      authError: null,
      
      // Conversations
      conversations: [],
      currentConversationId: null,
      messages: [],
      
      // Agents
      agents: [],
      enabledAgents: {}, // { agentId: boolean } - 사용자별 에이전트 활성화 상태
      
      // UI State
      isLoading: false,
      isStreaming: false,
      error: null,
      sidebarOpen: true,
      
      // Workflow Progress State
      workflowProgress: {
        isActive: false,
        currentStep: 0,
        totalSteps: 0,
        currentAgent: null,
        statusMessage: '',
        startTime: null
      },
      
      // Admin State
      activeTab: 'chat',  // 'chat' or 'admin'
      isRegistering: false,
      registrationError: null,
      
      // Auth Actions
      login: async (username, password) => {
        set({ authLoading: true, authError: null });
        
        try {
          const response = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
          });
          
          if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            
            set({
              user: data.user,
              isAuthenticated: true,
              authLoading: false,
              authError: null
            });
            
            return { success: true };
          } else {
            const error = await response.json();
            set({ authLoading: false, authError: error.detail || 'Login failed' });
            return { success: false, error: error.detail };
          }
        } catch (error) {
          set({ authLoading: false, authError: 'Network error' });
          return { success: false, error: 'Network error' };
        }
      },
      
      register: async (username, email, password, name) => {
        set({ authLoading: true, authError: null });
        
        try {
          const response = await fetch(`${API_BASE}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password, name })
          });
          
          if (response.ok) {
            set({ authLoading: false, authError: null });
            return { success: true };
          } else {
            const error = await response.json();
            set({ authLoading: false, authError: error.detail || 'Registration failed' });
            return { success: false, error: error.detail };
          }
        } catch (error) {
          set({ authLoading: false, authError: 'Network error' });
          return { success: false, error: 'Network error' };
        }
      },
      
      // Set token from K-Auth SSO callback
      setToken: async (token) => {
        localStorage.setItem('access_token', token);
        set({ isAuthenticated: true });
        
        // Fetch user info
        try {
          const response = await fetch(`${API_BASE}/api/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          
          if (response.ok) {
            const user = await response.json();
            set({ user, isAuthenticated: true });
          } else {
            console.error('Failed to fetch user info after K-Auth:', response.status);
          }
        } catch (error) {
          console.error('Error fetching user after K-Auth:', error);
        }
      },
      
      logout: async () => {
        const refreshToken = localStorage.getItem('refresh_token');
        
        try {
          if (refreshToken) {
            await fetch(`${API_BASE}/api/auth/logout`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
              },
              body: JSON.stringify({ refresh_token: refreshToken })
            });
          }
        } catch (error) {
          console.error('Logout error:', error);
        }
        
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        set({
          user: null,
          isAuthenticated: false,
          conversations: [],
          currentConversationId: null,
          messages: []
        });
      },
      
      checkAuth: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return;
        }
        
        try {
          const response = await fetch(`${API_BASE}/api/auth/me`, {
            headers: getAuthHeaders()
          });
          
          if (response.ok) {
            const user = await response.json();
            set({ user, isAuthenticated: true });
          } else {
            // Try to refresh token
            const refreshed = await get().refreshToken();
            if (!refreshed) {
              set({ user: null, isAuthenticated: false });
            }
          }
        } catch (error) {
          set({ user: null, isAuthenticated: false });
        }
      },
      
      refreshToken: async () => {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) return false;
        
        try {
          const response = await fetch(`${API_BASE}/api/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
          });
          
          if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            set({ user: data.user, isAuthenticated: true });
            return true;
          }
        } catch (error) {
          console.error('Token refresh failed:', error);
        }
        
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        return false;
      },
      
      clearAuthError: () => set({ authError: null }),
      
      // Helpers
      isAdmin: () => {
        const { user } = get();
        return user?.role === 'admin';
      },
      
      // Actions
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      
      setError: (error) => set({ error }),
      clearError: () => set({ error: null }),
  
  // Fetch conversations
  fetchConversations: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/chat/conversations`, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const conversations = await response.json();
        set({ conversations });
      }
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
    }
  },
  
  // Create new conversation
  createConversation: () => {
    set({
      currentConversationId: null,
      messages: []
    });
  },
  
  // Select conversation
  selectConversation: async (conversationId) => {
    set({ currentConversationId: conversationId, isLoading: true });
    
    try {
      const response = await fetch(`${API_BASE}/api/chat/conversations/${conversationId}`, {
        headers: getAuthHeaders()
      });
      if (response.ok) {
        const conversation = await response.json();
        set({
          messages: conversation.messages || [],
          isLoading: false
        });
      }
    } catch (error) {
      console.error('Failed to fetch conversation:', error);
      set({ isLoading: false, error: 'Failed to load conversation' });
    }
  },
  
  // Delete conversation
  deleteConversation: async (conversationId) => {
    try {
      const response = await fetch(`${API_BASE}/api/chat/conversations/${conversationId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        const { conversations, currentConversationId } = get();
        set({
          conversations: conversations.filter(c => c.id !== conversationId),
          ...(currentConversationId === conversationId && {
            currentConversationId: null,
            messages: []
          })
        });
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  },
  
  // Send message
  sendMessage: async (content) => {
    const { currentConversationId, messages } = get();
    const enabledAgentIds = get().getEnabledAgentIds();
    
    // Add user message immediately
    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };
    
    // Detect if this might be a multi-agent workflow
    const isMultiAgent = /그리고|후에|다음에|저장|정리|검색.*문서|이슈.*페이지/i.test(content);
    
    set({
      messages: [...messages, userMessage],
      isLoading: true,
      isStreaming: true,
      workflowProgress: {
        isActive: true,
        currentStep: 1,
        totalSteps: isMultiAgent ? 2 : 1,
        currentAgent: null,
        statusMessage: isMultiAgent ? '워크플로우 분석 중...' : '에이전트 연결 중...',
        startTime: Date.now()
      }
    });
    
    // Progress simulation for long-running requests
    const progressInterval = setInterval(() => {
      set((state) => {
        const elapsed = Date.now() - state.workflowProgress.startTime;
        let statusMessage = state.workflowProgress.statusMessage;
        let currentStep = state.workflowProgress.currentStep;
        
        if (elapsed > 5000 && elapsed <= 15000) {
          statusMessage = isMultiAgent ? '첫 번째 에이전트 실행 중...' : '에이전트 응답 대기 중...';
        } else if (elapsed > 15000 && elapsed <= 30000) {
          statusMessage = isMultiAgent ? '두 번째 에이전트 실행 중...' : '처리 중...';
          currentStep = isMultiAgent ? 2 : 1;
        } else if (elapsed > 30000) {
          statusMessage = '거의 완료되었습니다...';
        }
        
        return {
          workflowProgress: {
            ...state.workflowProgress,
            statusMessage,
            currentStep
          }
        };
      });
    }, 3000);
    
    try {
      const response = await fetch(`${API_BASE}/api/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          message: content,
          conversation_id: currentConversationId,
          enabled_agent_ids: enabledAgentIds  // 활성화된 에이전트만 전달
        })
      });
      
      clearInterval(progressInterval);
      
      if (response.ok) {
        const data = await response.json();
        
        // Add assistant message
        const assistantMessage = {
          id: data.id,
          role: 'assistant',
          content: data.content,
          timestamp: new Date().toISOString(),
          metadata: {
            agent: data.agent_used,
            taskState: data.task_state
          }
        };
        
        set((state) => ({
          messages: [...state.messages, assistantMessage],
          currentConversationId: data.conversation_id,
          isLoading: false,
          isStreaming: false,
          workflowProgress: {
            isActive: false,
            currentStep: 0,
            totalSteps: 0,
            currentAgent: null,
            statusMessage: '',
            startTime: null
          }
        }));
        
        // Refresh conversations list
        get().fetchConversations();
      } else {
        throw new Error('Failed to send message');
      }
    } catch (error) {
      clearInterval(progressInterval);
      console.error('Error sending message:', error);
      set({
        isLoading: false,
        isStreaming: false,
        workflowProgress: {
          isActive: false,
          currentStep: 0,
          totalSteps: 0,
          currentAgent: null,
          statusMessage: '',
          startTime: null
        },
        error: 'Failed to send message. Please try again.'
      });
    }
  },
  
  // Send message with streaming
  sendMessageStream: async (content) => {
    const { currentConversationId, messages } = get();
    const enabledAgentIds = get().getEnabledAgentIds();
    
    // Add user message immediately
    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };
    
    // Add placeholder for assistant message
    const assistantPlaceholder = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      metadata: { agent: null, streaming: true }
    };
    
    set({
      messages: [...messages, userMessage, assistantPlaceholder],
      isLoading: true,
      isStreaming: true
    });
    
    try {
      const response = await fetch(`${API_BASE}/api/chat/message/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          message: content,
          conversation_id: currentConversationId,
          enabled_agent_ids: enabledAgentIds  // 활성화된 에이전트만 전달
        })
      });
      
      if (!response.ok) throw new Error('Stream failed');
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let agentName = null;
      let conversationId = currentConversationId;
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('event:')) {
            // Handle event type
            continue;
          }
          
          if (line.startsWith('data:')) {
            try {
              const data = JSON.parse(line.slice(5).trim());
              
              if (data.conversation_id) {
                conversationId = data.conversation_id;
              }
              
              if (data.agent) {
                agentName = data.agent;
              }
              
              if (data.text) {
                set((state) => {
                  const msgs = [...state.messages];
                  const lastMsg = msgs[msgs.length - 1];
                  if (lastMsg.role === 'assistant') {
                    lastMsg.content += data.text;
                    lastMsg.metadata = { ...lastMsg.metadata, agent: agentName };
                  }
                  return { messages: msgs };
                });
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }
      
      // Mark streaming as complete
      set((state) => {
        const msgs = [...state.messages];
        const lastMsg = msgs[msgs.length - 1];
        if (lastMsg.role === 'assistant') {
          lastMsg.metadata = { ...lastMsg.metadata, streaming: false };
        }
        return {
          messages: msgs,
          currentConversationId: conversationId,
          isLoading: false,
          isStreaming: false
        };
      });
      
      // Refresh conversations
      get().fetchConversations();
      
    } catch (error) {
      console.error('Streaming error:', error);
      // Fallback to non-streaming
      set({ messages: messages.filter(m => m.role !== 'assistant' || m.content) });
      get().sendMessage(content);
    }
  },
  
  // Fetch agents and user preferences
  fetchAgents: async () => {
    try {
      // Fetch agents list
      const response = await fetch(`${API_BASE}/api/agents?include_offline=true`);
      if (response.ok) {
        const agents = await response.json();
        
        // Fetch user's agent preferences from DB
        let savedPreferences = {};
        try {
          const prefsResponse = await fetch(`${API_BASE}/api/user/preferences/agents`, {
            headers: getAuthHeaders()
          });
          if (prefsResponse.ok) {
            savedPreferences = await prefsResponse.json();
          }
        } catch (e) {
          console.log('No saved preferences found, using defaults');
        }
        
        // Merge with defaults (all enabled by default)
        const newEnabledAgents = {};
        agents.forEach(agent => {
          // If preference exists in DB, use it; otherwise default to true
          newEnabledAgents[agent.id] = savedPreferences[agent.id] !== undefined 
            ? savedPreferences[agent.id] 
            : true;
        });
        
        set({ agents, enabledAgents: newEnabledAgents });
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    }
  },
  
  // 에이전트 활성화/비활성화 토글 (일반 사용자용) - DB에 저장
  toggleAgentEnabled: async (agentId) => {
    const { enabledAgents } = get();
    const newEnabled = !enabledAgents[agentId];
    
    // Optimistic update
    set((state) => ({
      enabledAgents: {
        ...state.enabledAgents,
        [agentId]: newEnabled
      }
    }));
    
    // Save to DB
    try {
      await fetch(`${API_BASE}/api/user/preferences/agents/${agentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({ enabled: newEnabled })
      });
    } catch (error) {
      console.error('Failed to save agent preference:', error);
      // Revert on failure
      set((state) => ({
        enabledAgents: {
          ...state.enabledAgents,
          [agentId]: !newEnabled
        }
      }));
    }
  },
  
  // 활성화된 에이전트 목록 가져오기
  getEnabledAgentIds: () => {
    const { agents, enabledAgents } = get();
    return agents
      .filter(agent => enabledAgents[agent.id] !== false && agent.status === 'online')
      .map(agent => agent.id);
  },
  
  // Admin Actions
  setActiveTab: (tab) => set({ activeTab: tab }),
  
  // Register agent by URL (A2A Discovery) - Admin only
  registerAgentByUrl: async (url) => {
    set({ isRegistering: true, registrationError: null });
    
    try {
      const response = await fetch(`${API_BASE}/api/agents/register/url`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({ url })
      });
      
      if (response.ok) {
        const agent = await response.json();
        set((state) => ({
          agents: [...state.agents.filter(a => a.id !== agent.id), agent],
          isRegistering: false,
          registrationError: null
        }));
        return { success: true, agent };
      } else if (response.status === 401 || response.status === 403) {
        set({ 
          isRegistering: false, 
          registrationError: 'Admin access required'
        });
        return { success: false, error: 'Admin access required' };
      } else {
        const error = await response.json();
        set({ 
          isRegistering: false, 
          registrationError: error.detail || 'Failed to register agent'
        });
        return { success: false, error: error.detail };
      }
    } catch (error) {
      console.error('Failed to register agent:', error);
      set({ 
        isRegistering: false, 
        registrationError: 'Network error. Please check the URL and try again.'
      });
      return { success: false, error: 'Network error' };
    }
  },
  
  // Unregister agent - Admin only
  unregisterAgent: async (agentId) => {
    try {
      const response = await fetch(`${API_BASE}/api/agents/${agentId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });
      
      if (response.ok) {
        set((state) => ({
          agents: state.agents.filter(a => a.id !== agentId)
        }));
        return { success: true };
      } else if (response.status === 401 || response.status === 403) {
        return { success: false, error: 'Admin access required' };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail };
      }
    } catch (error) {
      console.error('Failed to unregister agent:', error);
      return { success: false, error: 'Network error' };
    }
  },
  
  // Clear registration error
  clearRegistrationError: () => set({ registrationError: null })
}),
    {
      name: 'agent-orchestrator-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        enabledAgents: state.enabledAgents  // 사용자 에이전트 설정 저장
      })
    }
  )
);

