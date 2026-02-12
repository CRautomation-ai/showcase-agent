import React, { useState } from "react";
import logo from "../assets/logo.png";
import { WELCOME_TEXT, UPLOAD_SUCCESS_TEXT } from "../constants/chat";
import { useChat } from "../hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { WelcomeView } from "./WelcomeView";
import { ChatInput } from "./ChatInput";
import { LoadingDots } from "./LoadingDots";

interface ChatInterfaceProps {
  onUnauthorized?: () => void;
  onLogout?: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onUnauthorized, onLogout }) => {
  const {
    messages,
    setMessages,
    input,
    setInput,
    loading,
    error,
    setError,
    messagesEndRef,
    handleSubmit,
  } = useChat(onUnauthorized);

  const [documentsLoaded, setDocumentsLoaded] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const isWelcomeOnly =
    messages.length === 1 &&
    messages[0].role === "assistant" &&
    messages[0].content === WELCOME_TEXT;

  const handleUploadComplete = () => {
    setDocumentsLoaded(true);
    // Replace the welcome message with upload success message
    setMessages([{ role: "assistant", content: UPLOAD_SUCCESS_TEXT }]);
  };

  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage);
  };

  const handleResetDocs = () => {
    setDocumentsLoaded(false);
    setMessages([{ role: "assistant", content: WELCOME_TEXT }]);
    setError(null);
  };

  return (
    <div className="app-container">
      <div className="header">
        <button type="button" className="reset-button" onClick={handleResetDocs}>
          Reset Doc
        </button>
        <img src={logo} alt="Showcase Agent" className="header-logo" />
        {onLogout && (
          <button type="button" className="logout-button" onClick={onLogout}>
            Log out
          </button>
        )}
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="messages-container">
        {isWelcomeOnly && !documentsLoaded ? (
          <WelcomeView 
            onUploadComplete={handleUploadComplete}
            onUploadError={handleUploadError}
            onUploadingChange={setIsUploading}
          />
        ) : (
          <>
            {messages.map((msg, i) => (
              <MessageBubble key={i} message={msg} />
            ))}
          </>
        )}
        {loading && <LoadingDots />}
        <div ref={messagesEndRef} />
      </div>

      <ChatInput
        value={input}
        onChange={setInput}
        onSubmit={handleSubmit}
        loading={loading}
        disabled={isUploading}
      />
    </div>
  );
};

export default ChatInterface;
