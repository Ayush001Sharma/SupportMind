/**
 * ChatContainer.test.tsx — Integration tests for the full chat interface.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ChatContainer } from '../components/chat/ChatContainer';
import { ChatProvider } from '../context/ChatContext';

vi.mock('../hooks/useChat', () => ({
  useChat: vi.fn(),
}));

import { useChat } from '../hooks/useChat';
const mockUseChat = useChat as ReturnType<typeof vi.fn>;

const renderWithProviders = (ui: React.ReactElement) => {
  return render(<ChatProvider>{ui}</ChatProvider>);
};

describe('ChatContainer', () => {
  beforeEach(() => {
    mockUseChat.mockReturnValue({
      messages: [],
      sendMessage: vi.fn(),
      isSending: false,
      error: null,
    });
  });

  it('renders empty state with welcome prompt', () => {
    renderWithProviders(<ChatContainer />);
    expect(screen.getByText(/how can i help/i)).toBeInTheDocument();
  });

  it('renders the chat input', () => {
    renderWithProviders(<ChatContainer />);
    expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument();
  });

  it('calls sendMessage when user types and presses Enter', async () => {
    const sendMessage = vi.fn();
    mockUseChat.mockReturnValue({
      messages: [],
      sendMessage,
      isSending: false,
      error: null,
    });
    const user = userEvent.setup();
    renderWithProviders(<ChatContainer />);
    const textarea = screen.getByPlaceholderText(/ask a question/i);
    await user.type(textarea, 'What are your hours?');
    await user.keyboard('{Enter}');
    expect(sendMessage).toHaveBeenCalledWith('What are your hours?');
  });

  it('renders user messages', () => {
    mockUseChat.mockReturnValue({
      messages: [{ id: '1', role: 'user', content: 'Test user message' }],
      sendMessage: vi.fn(),
      isSending: false,
      error: null,
    });
    renderWithProviders(<ChatContainer />);
    expect(screen.getByText('Test user message')).toBeInTheDocument();
  });

  it('renders assistant messages', () => {
    mockUseChat.mockReturnValue({
      messages: [
        { id: '2', role: 'assistant', content: 'The answer is 42.', sources: [], fallback_used: false },
      ],
      sendMessage: vi.fn(),
      isSending: false,
      error: null,
    });
    renderWithProviders(<ChatContainer />);
    expect(screen.getByText(/answer is 42/i)).toBeInTheDocument();
  });

  it('disables input while sending', () => {
    mockUseChat.mockReturnValue({
      messages: [],
      sendMessage: vi.fn(),
      isSending: true,
      error: null,
    });
    renderWithProviders(<ChatContainer />);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('shows error banner when error is set', () => {
    mockUseChat.mockReturnValue({
      messages: [],
      sendMessage: vi.fn(),
      isSending: false,
      error: 'Network request failed.',
    });
    renderWithProviders(<ChatContainer />);
    expect(screen.getByText(/network request failed/i)).toBeInTheDocument();
  });

  it('hides empty state when messages exist', () => {
    mockUseChat.mockReturnValue({
      messages: [{ id: '1', role: 'user', content: 'Hello' }],
      sendMessage: vi.fn(),
      isSending: false,
      error: null,
    });
    renderWithProviders(<ChatContainer />);
    expect(screen.queryByText(/how can i help/i)).not.toBeInTheDocument();
  });

  it('renders loading indicator for loading message', () => {
    mockUseChat.mockReturnValue({
      messages: [
        { id: '3', role: 'assistant', content: '', isLoading: true },
      ],
      sendMessage: vi.fn(),
      isSending: false,
      error: null,
    });
    const { container } = renderWithProviders(<ChatContainer />);
    expect(container.querySelectorAll('.animate-pulse-slow').length).toBeGreaterThan(0);
  });
});
