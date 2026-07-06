import React, { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { useChat } from '../../hooks/useChat';
import { BotMessageSquare } from 'lucide-react';

export const ChatContainer: React.FC = () => {
  const { messages, sendMessage, isSending, error } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex flex-col h-full w-full max-w-5xl mx-auto px-4 py-6">
      <div className="flex-1 overflow-y-auto scrollbar-hide pb-32">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-4 animate-fade-in">
            <div className="w-16 h-16 bg-surface border border-border rounded-2xl flex items-center justify-center mb-6 shadow-xl">
              <BotMessageSquare size={32} className="text-primary" />
            </div>
            <h2 className="text-2xl font-semibold text-text mb-2">How can I help you today?</h2>
            <p className="text-muted max-w-md">
              Ask me anything about the documents you've uploaded. I'll provide answers directly from your knowledge base.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="fixed bottom-0 left-0 lg:left-64 right-0 p-4 bg-gradient-to-t from-background via-background to-transparent pt-10">
        {error && (
          <div className="max-w-4xl mx-auto mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm text-center animate-slide-up">
            {error}
          </div>
        )}
        <ChatInput onSend={sendMessage} disabled={isSending} />
        <div className="text-center mt-3 text-xs text-muted/60">
          Answers are generated entirely from uploaded documents.
        </div>
      </div>
    </div>
  );
};
