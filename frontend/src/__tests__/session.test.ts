/**
 * session.test.ts — Tests for localStorage session ID management.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { getSessionId, resetSessionId } from '../utils/session';

describe('Session Management', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('generates a session ID when none exists', () => {
    const id = getSessionId();
    expect(id).toBeTruthy();
    expect(typeof id).toBe('string');
  });

  it('generated ID is a valid UUID format', () => {
    const id = getSessionId();
    const uuidRegex =
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    expect(id).toMatch(uuidRegex);
  });

  it('persists session ID to localStorage', () => {
    const id = getSessionId();
    expect(localStorage.getItem('chat_session_id')).toBe(id);
  });

  it('returns the same session ID on subsequent calls', () => {
    const id1 = getSessionId();
    const id2 = getSessionId();
    expect(id1).toBe(id2);
  });

  it('resetSessionId creates a new different ID', () => {
    const original = getSessionId();
    const newId = resetSessionId();
    expect(newId).not.toBe(original);
  });

  it('resetSessionId persists the new ID to localStorage', () => {
    const newId = resetSessionId();
    expect(localStorage.getItem('chat_session_id')).toBe(newId);
  });

  it('getSessionId returns the reset ID after reset', () => {
    const newId = resetSessionId();
    const retrieved = getSessionId();
    expect(retrieved).toBe(newId);
  });
});
