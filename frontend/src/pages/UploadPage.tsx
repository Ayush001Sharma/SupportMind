import React from 'react';
import { DocumentUploader } from '../components/document/DocumentUploader';

export const UploadPage: React.FC = () => {
  return (
    <div className="h-full flex items-center justify-center p-6 bg-gradient-to-br from-background to-surface/50">
      <DocumentUploader />
    </div>
  );
};
