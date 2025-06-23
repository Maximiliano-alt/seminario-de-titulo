import React from 'react';

interface CodeViewerProps {
  code: string;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({ code }) => {
  return (
    <pre className="code-viewer">
      <code>{code}</code>
    </pre>
  );
};
