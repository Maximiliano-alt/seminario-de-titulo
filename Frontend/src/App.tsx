import React from 'react';
import { CodeGenerator } from './components/CodeGenerator';
import './styles.css';

const App: React.FC = () => {
  return (
    <div className="app">
      <header>
        <h1>Code Generation with Embeddings</h1>
        <p>Enter a user story and UML diagram to generate code with context-aware responses</p>
      </header>
      <main>
        <CodeGenerator />
      </main>
    </div>
  );
};

export default App; 