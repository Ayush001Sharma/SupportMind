/**
 * DocumentUploader.test.tsx — Tests for the file upload component.
 */

import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { DocumentUploader } from '../components/document/DocumentUploader';

vi.mock('../hooks/useUpload', () => ({
  useUpload: vi.fn(),
}));

import { useUpload } from '../hooks/useUpload';

const mockUseUpload = useUpload as ReturnType<typeof vi.fn>;

const idleState = {
  uploadFile: vi.fn(),
  isUploading: false,
  error: null,
  successData: null,
  resetUploadState: vi.fn(),
};

describe('DocumentUploader', () => {
  beforeEach(() => {
    mockUseUpload.mockReturnValue({ ...idleState, uploadFile: vi.fn(), resetUploadState: vi.fn() });
  });

  it('renders the upload zone', () => {
    render(<DocumentUploader />);
    expect(screen.getByText(/drag & drop/i)).toBeInTheDocument();
  });

  it('renders "Browse Files" button', () => {
    render(<DocumentUploader />);
    expect(screen.getByText(/browse files/i)).toBeInTheDocument();
  });

  it('shows supported formats text', () => {
    render(<DocumentUploader />);
    expect(screen.getByText(/pdf, docx, txt/i)).toBeInTheDocument();
  });

  it('shows uploading spinner when isUploading=true', () => {
    mockUseUpload.mockReturnValue({ ...idleState, isUploading: true });
    render(<DocumentUploader />);
    expect(screen.getByText(/uploading and processing/i)).toBeInTheDocument();
  });

  it('shows success message after successful upload', () => {
    mockUseUpload.mockReturnValue({
      ...idleState,
      successData: {
        document_id: 'abc-123',
        filename: 'policy.pdf',
        document_type: 'pdf',
        file_size: 1024,
        upload_timestamp: '2026-07-06T00:00:00Z',
        status: 'indexed',
      },
    });
    render(<DocumentUploader />);
    expect(screen.getByText(/upload successful/i)).toBeInTheDocument();
    expect(screen.getByText(/policy\.pdf/i)).toBeInTheDocument();
  });

  it('shows "Upload Another" button after success', () => {
    mockUseUpload.mockReturnValue({
      ...idleState,
      successData: {
        document_id: 'xyz',
        filename: 'guide.txt',
        document_type: 'txt',
        file_size: 512,
        upload_timestamp: '2026-07-06T00:00:00Z',
        status: 'indexed',
      },
    });
    render(<DocumentUploader />);
    expect(screen.getByText(/upload another/i)).toBeInTheDocument();
  });

  it('calls resetUploadState when "Upload Another" is clicked', async () => {
    const resetFn = vi.fn();
    mockUseUpload.mockReturnValue({
      ...idleState,
      resetUploadState: resetFn,
      successData: {
        document_id: 'xyz',
        filename: 'guide.txt',
        document_type: 'txt',
        file_size: 512,
        upload_timestamp: '2026-07-06T00:00:00Z',
        status: 'indexed',
      },
    });
    const user = userEvent.setup();
    render(<DocumentUploader />);
    await user.click(screen.getByText(/upload another/i));
    expect(resetFn).toHaveBeenCalled();
  });

  it('shows error message when error is set', () => {
    mockUseUpload.mockReturnValue({
      ...idleState,
      error: 'File upload failed. Server returned 413.',
    });
    render(<DocumentUploader />);
    expect(screen.getByRole('heading', { name: /upload failed/i })).toBeInTheDocument();
    expect(screen.getByText(/413/)).toBeInTheDocument();
  });
});
