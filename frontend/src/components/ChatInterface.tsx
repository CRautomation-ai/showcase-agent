import React, { useState } from "react";
import logo from "../assets/logo.jpg";
import { WELCOME_TEXT } from "../constants/chat";
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
    input,
    setInput,
    loading,
    error,
    setError,
    messagesEndRef,
    handleSubmit,
  } = useChat(onUnauthorized);

  const [documentsLoaded, setDocumentsLoaded] = useState(false);

  const isWelcomeOnly =
    messages.length === 1 &&
    messages[0].role === "assistant" &&
    messages[0].content === WELCOME_TEXT;

  const handleUploadComplete = () => {
    setDocumentsLoaded(true);
  };

  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage);
  };

  return (
    <div className="app-container">
      <div className="header">
        <img src={logo} alt="SOP RAG" className="header-logo" />
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
      />
    </div>
  );
};

export default ChatInterface;
