import React from "react";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (e: React.FormEvent<HTMLFormElement>) => void;
  loading: boolean;
  placeholder?: string;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSubmit,
  loading,
  placeholder = "Ask the agent...",
  disabled = false,
}) => {
  const isDisabled = loading || disabled;
  
  return (
    <div className={`input-container ${isDisabled ? "disabled" : ""}`}>
      <form onSubmit={onSubmit} className="input-form">
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={isDisabled ? "Please wait..." : placeholder}
          className="input-field"
          disabled={isDisabled}
        />
        <button
          type="submit"
          disabled={isDisabled || !value.trim()}
          className="send-button"
        >
          Send
        </button>
      </form>
    </div>
  );
};
