import React from "react";
import { WELCOME_TEXT } from "../constants/chat";
import { FileUpload } from "./FileUpload";

interface WelcomeViewProps {
  onUploadComplete?: () => void;
  onUploadError?: (error: string) => void;
}

export const WelcomeView: React.FC<WelcomeViewProps> = ({
  onUploadComplete,
  onUploadError,
}) => (
  <div className="welcome-center">
    <div className="welcome-content">
      <p className="welcome-text">{WELCOME_TEXT}</p>
      <div className="welcome-upload-section">
        <p className="welcome-upload-title">
          Upload documents to get started
        </p>
        <FileUpload
          onUploadComplete={onUploadComplete}
          onUploadError={onUploadError}
        />
      </div>
    </div>
  </div>
);
