/**
 * MessageBubble.test.tsx — Tests for the chat message rendering component.
 */

import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { MessageBubble } from '../components/chat/MessageBubble';
import type { ChatMessage } from '../context/ChatContext';

const userMessage: ChatMessage = {
  id: 'msg-1',
  role: 'user',
  content: 'What is the return policy?',
};

const assistantMessage: ChatMessage = {
  id: 'msg-2',
  role: 'assistant',
  content: 'Returns are accepted within **30 days** of purchase.',
  sources: [{ filename: 'policy.pdf', page_number: 3 }],
  fallback_used: false,
};

const loadingMessage: ChatMessage = {
  id: 'msg-3',
  role: 'assistant',
  content: '',
  isLoading: true,
};

const fallbackMessage: ChatMessage = {
  id: 'msg-4',
  role: 'assistant',
  content: "I don't know.",
  fallback_used: true,
  sources: [],
};

describe('MessageBubble', () => {
  it('renders user message content', () => {
    render(<MessageBubble message={userMessage} />);
    expect(screen.getByText('What is the return policy?')).toBeInTheDocument();
  });

  it('renders assistant message content', () => {
    render(<MessageBubble message={assistantMessage} />);
    expect(screen.getByText(/30 days/)).toBeInTheDocument();
  });

  it('renders loading indicator when isLoading is true', () => {
    const { container } = render(<MessageBubble message={loadingMessage} />);
    expect(container.querySelectorAll('.animate-pulse-slow').length).toBeGreaterThan(0);
  });

  it('does NOT render text when loading', () => {
    render(<MessageBubble message={loadingMessage} />);
    expect(screen.queryByText(/returns/i)).not.toBeInTheDocument();
  });

  it('renders source citation filename', () => {
    render(<MessageBubble message={assistantMessage} />);
    expect(screen.getByText(/policy\.pdf/)).toBeInTheDocument();
  });

  it('renders source citation page number', () => {
    render(<MessageBubble message={assistantMessage} />);
    expect(screen.getByText(/Pg 3/)).toBeInTheDocument();
  });

  it('does not render sources section when sources array is empty', () => {
    render(<MessageBubble message={fallbackMessage} />);
    expect(screen.queryByText(/Sources/i)).not.toBeInTheDocument();
  });

  it('renders fallback message text naturally', () => {
    render(<MessageBubble message={fallbackMessage} />);
    expect(screen.getByText(/I don't know/i)).toBeInTheDocument();
  });
});
