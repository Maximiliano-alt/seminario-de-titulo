import React from 'react';

interface UserStoryInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  isGenerating: boolean;
}

export const UserStoryInput: React.FC<UserStoryInputProps> = ({ 
  value, 
  onChange, 
  placeholder = "Como [tipo de usuario], quiero [una acción] para que [un beneficio/valor]...",
  isGenerating
}) => {
  return (
    <div className="user-story-input">
      <label htmlFor="userStory" className="control-label">
        Historia de Usuario
      </label>
      <p className="description">
        Describa los requisitos desde la perspectiva del usuario.
      </p>
      <textarea
        id="userStory"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={6}
        className="user-story-textarea"
        required
        disabled={isGenerating}
      />
      <div className="input-info">
        <span className="char-count">{value.length} caracteres</span>
      </div>
    </div>
  );
};

export default UserStoryInput; 