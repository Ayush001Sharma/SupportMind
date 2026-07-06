import { useState } from 'react';
import { DocumentAPI } from '../api/client';
import type { UploadResponse } from '../api/client';

export const useUpload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successData, setSuccessData] = useState<UploadResponse | null>(null);

  const uploadFile = async (file: File) => {
    setIsUploading(true);
    setError(null);
    setSuccessData(null);

    try {
      const response = await DocumentAPI.uploadDocument(file);
      setSuccessData(response);
      return response;
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'File upload failed. Please try again.');
      throw err;
    } finally {
      setIsUploading(false);
    }
  };

  const resetUploadState = () => {
    setError(null);
    setSuccessData(null);
    setIsUploading(false);
  };

  return {
    uploadFile,
    isUploading,
    error,
    successData,
    resetUploadState,
  };
};
