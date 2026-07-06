import axios from 'axios';

// Default to local backend if env var is missing
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface SourceAttribution {
  filename: string;
  page_number: number;
}

export interface ChatResponse {
  answer: string;
  sources: SourceAttribution[];
  response_time_ms: number;
  fallback_used: boolean;
}

export interface UploadResponse {
  document_id: string;
  filename: string;
  document_type: string;
  file_size: number;
  upload_timestamp: string;
  status: string;
}

export const ChatAPI = {
  sendMessage: async (sessionId: string, message: string): Promise<ChatResponse> => {
    const response = await apiClient.post<ChatResponse>('/chat/message', {
      session_id: sessionId,
      message,
    });
    return response.data;
  },
};

export const DocumentAPI = {
  uploadDocument: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post<UploadResponse>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};
