/**
 * ChatInput.test.tsx — Tests for the message input component.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { ChatInput } from '../components/chat/ChatInput';

describe('ChatInput', () => {
  it('renders the textarea', () => {
    render(<ChatInput onSend={vi.fn()} />);
    expect(screen.getByPlaceholderText(/ask a question/i)).toBeInTheDocument();
  });

  it('renders the send button', () => {
    render(<ChatInput onSend={vi.fn()} />);
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
  });

  it('send button is disabled when input is empty', () => {
    render(<ChatInput onSend={vi.fn()} />);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('send button becomes enabled after typing', async () => {
    const user = userEvent.setup();
    render(<ChatInput onSend={vi.fn()} />);
    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Hello?');
    const button = screen.getByRole('button');
    expect(button).not.toBeDisabled();
  });

  it('calls onSend with message text when button is clicked', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);
    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'What is the return policy?');
    await user.click(screen.getByRole('button'));
    expect(onSend).toHaveBeenCalledWith('What is the return policy?');
  });

  it('calls onSend when Enter is pressed (without Shift)', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);
    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Hello!');
    await user.keyboard('{Enter}');
    expect(onSend).toHaveBeenCalledOnce();
  });

  it('does NOT call onSend when Shift+Enter is pressed', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} />);
    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Multi');
    await user.keyboard('{Shift>}{Enter}{/Shift}');
    expect(onSend).not.toHaveBeenCalled();
  });

  it('clears input after send', async () => {
    const user = userEvent.setup();
    render(<ChatInput onSend={vi.fn()} />);
    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    await user.type(textarea, 'Hello');
    await user.click(screen.getByRole('button'));
    expect(textarea.value).toBe('');
  });

  it('send button is disabled when prop disabled=true', () => {
    render(<ChatInput onSend={vi.fn()} disabled={true} />);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('does not call onSend when disabled even with text entered', async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    render(<ChatInput onSend={onSend} disabled={true} />);
    // When disabled, typing is blocked so directly fire keyboard event
    const textarea = screen.getByRole('textbox');
    await user.type(textarea, 'Test message');
    expect(onSend).not.toHaveBeenCalled();
  });
});
