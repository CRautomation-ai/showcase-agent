import React from "react";
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
      <p className="welcome-text">Upload documents to get started</p>
      <FileUpload
        onUploadComplete={onUploadComplete}
        onUploadError={onUploadError}
      />
    </div>
  </div>
);
