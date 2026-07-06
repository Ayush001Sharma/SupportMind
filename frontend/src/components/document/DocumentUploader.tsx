import React, { useCallback, useState } from 'react';
import { UploadCloud, CheckCircle, AlertCircle } from 'lucide-react';
import { useUpload } from '../../hooks/useUpload';
import { clsx } from 'clsx';

export const DocumentUploader: React.FC = () => {
  const { uploadFile, isUploading, error, successData, resetUploadState } = useUpload();
  const [isDragActive, setIsDragActive] = useState(false);

  const handleFileChange = async (file: File | undefined) => {
    if (!file) return;
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
    ];
    if (!allowedTypes.includes(file.type)) {
      alert('Only PDF, DOCX, and TXT files are supported.');
      return;
    }
    await uploadFile(file);
  };

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragActive(false);
      const file = e.dataTransfer.files[0];
      handleFileChange(file);
    },
    [uploadFile]
  );

  return (
    <div className="w-full max-w-2xl mx-auto mt-12 animate-slide-up">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-text mb-3">Upload Knowledge</h2>
        <p className="text-muted">
          Add PDFs, Word documents, or text files to train the assistant.
        </p>
      </div>

      <div
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={clsx(
          'glass-panel p-10 flex flex-col items-center justify-center border-2 border-dashed transition-all duration-300 relative overflow-hidden',
          isDragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50',
          isUploading && 'pointer-events-none opacity-80'
        )}
      >
        {isUploading ? (
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="w-16 h-16 border-4 border-surface border-t-primary rounded-full animate-spin"></div>
            <p className="text-lg font-medium text-text">Uploading and Processing...</p>
            <p className="text-sm text-muted">Extracting text and generating vectors.</p>
          </div>
        ) : successData ? (
          <div className="flex flex-col items-center justify-center space-y-4 animate-fade-in text-center">
            <div className="w-16 h-16 bg-emerald-500/20 rounded-full flex items-center justify-center text-emerald-400 mb-2 shadow-inner border border-emerald-500/30">
              <CheckCircle size={32} />
            </div>
            <p className="text-xl font-medium text-text">Upload Successful</p>
            <p className="text-sm text-muted">
              <span className="font-semibold text-text">{successData.filename}</span> has been indexed.
            </p>
            <button
              onClick={resetUploadState}
              className="mt-6 px-6 py-2.5 bg-surface border border-border rounded-xl text-text hover:bg-surface/80 transition-colors"
            >
              Upload Another
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center space-y-6 text-center">
            <div className="w-20 h-20 bg-surface rounded-full flex items-center justify-center shadow-inner border border-border">
              <UploadCloud size={40} className="text-primary" />
            </div>
            <div>
              <p className="text-lg font-medium text-text mb-1">
                Drag & drop your file here
              </p>
              <p className="text-sm text-muted mb-6">
                Supports PDF, DOCX, TXT up to 10MB
              </p>
            </div>
            <label className="px-6 py-3 bg-primary text-white rounded-xl cursor-pointer hover:bg-primary-hover transition-colors font-medium shadow-lg shadow-primary/25">
              Browse Files
              <input
                type="file"
                className="hidden"
                accept=".pdf,.docx,.txt"
                onChange={(e) => handleFileChange(e.target.files?.[0])}
              />
            </label>
          </div>
        )}
      </div>
      
      {error && (
        <div className="mt-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-3 animate-slide-up">
          <AlertCircle className="text-red-400 mt-0.5 flex-shrink-0" size={20} />
          <div>
            <h4 className="text-red-400 font-medium">Upload Failed</h4>
            <p className="text-red-400/80 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}
    </div>
  );
};
