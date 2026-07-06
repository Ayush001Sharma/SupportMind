import React from 'react';
import { ChatContainer } from '../components/chat/ChatContainer';
import { ChatProvider } from '../context/ChatContext';

export const ChatPage: React.FC = () => {
  return (
    <div className="h-full relative overflow-hidden">
      <ChatProvider>
        <ChatContainer />
      </ChatProvider>
    </div>
  );
};
