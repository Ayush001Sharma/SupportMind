export const getSessionId = (): string => {
  let sessionId = localStorage.getItem('chat_session_id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('chat_session_id', sessionId);
  }
  return sessionId;
};

export const resetSessionId = (): string => {
  const newSessionId = crypto.randomUUID();
  localStorage.setItem('chat_session_id', newSessionId);
  return newSessionId;
};
