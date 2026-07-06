import React from 'react';
import ReactMarkdown from 'react-markdown';
import { clsx } from 'clsx';
import { Bot, FileText } from 'lucide-react';
import type { ChatMessage } from '../../context/ChatContext';

export const MessageBubble: React.FC<{ message: ChatMessage }> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div
      className={clsx(
        'flex w-full animate-fade-in group',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={clsx(
          'flex max-w-[85%] sm:max-w-[75%] gap-4 p-4 md:p-6 rounded-2xl shadow-sm transition-all',
          isUser
            ? 'bg-primary text-white rounded-br-none'
            : 'glass-panel text-text rounded-bl-none'
        )}
      >
        {!isUser && (
          <div className="flex-shrink-0 mt-1">
            <div className="w-8 h-8 rounded-full bg-surface flex items-center justify-center border border-border shadow-inner">
              <Bot size={18} className="text-primary" />
            </div>
          </div>
        )}

        <div className="flex-1 overflow-hidden">
          {message.isLoading ? (
            <div className="flex space-x-2 items-center h-6">
              <div className="w-2 h-2 bg-muted rounded-full animate-pulse-slow"></div>
              <div className="w-2 h-2 bg-muted rounded-full animate-pulse-slow delay-75"></div>
              <div className="w-2 h-2 bg-muted rounded-full animate-pulse-slow delay-150"></div>
            </div>
          ) : (
            <div className="prose prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-surface prose-pre:border-border prose-pre:border text-sm sm:text-base">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}

          {/* Sources Section */}
          {!isUser && !message.isLoading && message.sources && message.sources.length > 0 && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <span className="text-xs font-semibold text-muted tracking-wider uppercase mb-2 block">
                Sources
              </span>
              <div className="flex flex-wrap gap-2">
                {message.sources.map((source, idx) => (
                  <div
                    key={idx}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-surface/50 border border-border text-xs text-muted hover:text-text hover:bg-surface transition-colors cursor-default"
                  >
                    <FileText size={12} />
                    <span className="truncate max-w-[150px]">{source.filename}</span>
                    <span className="opacity-50">·</span>
                    <span>Pg {source.page_number}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
