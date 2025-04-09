import React from 'react';

interface UMLDiagramEditorProps {
  value: string;
  onChange: (value: string) => void;
}

export const UMLDiagramEditor: React.FC<UMLDiagramEditorProps> = ({ value, onChange }) => {
  return (
    <textarea
      className="uml-editor"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Enter UML diagram here..."
    />
  );
};
