import React from 'react';

interface UserStoryInputProps {
  value: string;
  onChange: (value: string) => void;
}

const UserStoryInput: React.FC<UserStoryInputProps> = ({ value, onChange }) => {
  return (
    <div className="input-container">
      <h2>User Story</h2>
      <p className="description">
        Describe the requirements from a user's perspective.
      </p>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="As a [type of user], I want [an action] so that [a benefit/value]..."
        rows={6}
        className="input-textarea"
      />
    </div>
  );
};

export default UserStoryInput; 