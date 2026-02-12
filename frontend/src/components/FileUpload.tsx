import React, { useRef, useState, useCallback } from "react";
import { API_BASE_URL, AUTH_TOKEN_KEY } from "../constants/chat";
import { Spinner } from "./Spinner";

interface FileUploadProps {
  onUploadComplete?: (result: UploadResult) => void;
  onUploadError?: (error: string) => void;
  onUploadingChange?: (uploading: boolean) => void;
}

interface UploadResult {
  message: string;
  files_processed: number;
  chunks_processed: number;
  filenames: string[];
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onUploadComplete,
  onUploadError,
  onUploadingChange,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;

      const supportedTypes = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
      ];

      const validFiles: File[] = [];
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const ext = file.name.split(".").pop()?.toLowerCase();
        if (
          supportedTypes.includes(file.type) ||
          ext === "pdf" ||
          ext === "docx" ||
          ext === "doc"
        ) {
          validFiles.push(file);
        }
      }

      if (validFiles.length === 0) {
        onUploadError?.("Please upload PDF or Word documents (.pdf, .docx, .doc)");
        return;
      }

      setIsUploading(true);
      onUploadingChange?.(true);
      setUploadStatus(`Uploading ${validFiles.length} file(s)...`);

      try {
        const formData = new FormData();
        validFiles.forEach((file) => {
          formData.append("files", file);
        });

        const token = localStorage.getItem(AUTH_TOKEN_KEY);
        const response = await fetch(`${API_BASE_URL}/upload`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
        }

        const result: UploadResult = await response.json();
        setUploadStatus(
          `Successfully processed ${result.files_processed} file(s) with ${result.chunks_processed} chunks`
        );
        onUploadComplete?.(result);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Upload failed";
        setUploadStatus(null);
        onUploadError?.(message);
      } finally {
        setIsUploading(false);
        onUploadingChange?.(false);
      }
    },
    [onUploadComplete, onUploadError, onUploadingChange]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleUpload(e.dataTransfer.files);
    },
    [handleUpload]
  );

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleUpload(e.target.files);
    // Reset input so the same file can be selected again
    e.target.value = "";
  };

  return (
    <div className="file-upload-container">
      <div
        className={`file-upload-dropzone ${isDragging ? "dragging" : ""} ${
          isUploading ? "uploading" : ""
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={isUploading ? undefined : handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.doc"
          onChange={handleFileChange}
          style={{ display: "none" }}
        />
        {isUploading ? (
          <div className="upload-progress">
            <Spinner />
            <span>{uploadStatus}</span>
          </div>
        ) : (
          <>
            <div className="upload-icon">
              <svg
                width="32"
                height="32"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <p className="upload-text">
              <span className="upload-text-main">
                Drop files here or click to upload
              </span>
              <span className="upload-text-sub">
                PDF, DOCX, DOC files supported
              </span>
            </p>
          </>
        )}
      </div>
      {uploadStatus && !isUploading && (
        <div className="upload-status success">{uploadStatus}</div>
      )}
    </div>
  );
};
