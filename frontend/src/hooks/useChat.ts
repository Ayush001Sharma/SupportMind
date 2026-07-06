import { useState } from 'react';
import { ChatAPI } from '../api/client';
import { useChatContext } from '../context/ChatContext';
import { getSessionId } from '../utils/session';

export const useChat = () => {
  const { messages, addMessage, updateMessage } = useChatContext();
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMessageId = crypto.randomUUID();
    addMessage({ id: userMessageId, role: 'user', content: text });

    const assistantMessageId = crypto.randomUUID();
    addMessage({ id: assistantMessageId, role: 'assistant', content: '', isLoading: true });

    setIsSending(true);
    setError(null);

    try {
      const sessionId = getSessionId();
      const response = await ChatAPI.sendMessage(sessionId, text);

      updateMessage(assistantMessageId, {
        content: response.answer,
        sources: response.sources,
        fallback_used: response.fallback_used,
        isLoading: false,
      });
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Failed to send message. Please try again.');
      updateMessage(assistantMessageId, {
        content: "I'm sorry, I encountered an error while processing your request.",
        isLoading: false,
      });
    } finally {
      setIsSending(false);
    }
  };

  return {
    messages,
    sendMessage,
    isSending,
    error,
  };
};
