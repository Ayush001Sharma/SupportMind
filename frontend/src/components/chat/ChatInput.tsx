import React, { useState, useRef, useEffect } from 'react';
import { SendHorizontal } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSend, disabled }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!input.trim() || disabled) return;
    onSend(input);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  return (
    <div className="relative flex items-end w-full max-w-4xl mx-auto glass-panel p-2">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question about your documents..."
        disabled={disabled}
        className="w-full bg-transparent text-text placeholder:text-muted/60 resize-none outline-none max-h-[200px] py-3 px-4 scrollbar-hide"
        rows={1}
      />
      <button
        onClick={handleSend}
        disabled={!input.trim() || disabled}
        className="absolute right-4 bottom-3 p-2 rounded-xl bg-primary text-white disabled:opacity-50 disabled:bg-surface disabled:text-muted transition-all hover:bg-primary-hover active:scale-95"
      >
        <SendHorizontal size={20} />
      </button>
    </div>
  );
};
