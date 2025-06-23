import React from 'react';
import { Toaster } from 'react-hot-toast';
import { EnhancedCodeGenerator } from './components/EnhancedCodeGenerator';
import './styles.css';

const App: React.FC = () => {
  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>HERRAMIENTA PARA LA GENERACIÓN DE DIAGRAMAS DE CLASE Y CÓDIGO DESDE HISTORIAS DE USUARIO BASADO EN MODELOS GRANDES DE LENGUAJE</h1>
          <h2> "Story UMLify" - MVP 2.0</h2>
          <p>Historia de usuario → Diagrama UML → Código Java</p>
          <p>Integración con Claude 3.5, Gemini 2.0, DeepSeek R1, GPT-4o y GPT-4o-mini</p>
          <div className="feature-badges">
            <span className="badge">Soporte Multi-LLM</span>
            <span className="badge">Análisis de Dominio</span>
            <span className="badge">Vista Previa UML</span>
            <span className="badge">Código Descargable</span>
          </div>
        </div>
      </header>
      
      <main className="app-main">
        <EnhancedCodeGenerator />
      </main>
      
      <footer className="app-footer">
        <div className="footer-content">
          <div className="footer-description">
            <h3>Proyecto de Seminario de Título</h3>
            <p>
              Esta herramienta representa la integración desarrollada por <strong>Maximiliano Espindola </strong> 
              como parte de su Seminario de Título. El proyecto implementa un sistema innovador que combina 
              múltiples modelos de lenguaje grande (LLM) para automatizar la generación de diagramas UML y 
              código Java a partir de historias de usuario.
            </p>
            <div className="poster-link">
              <p>📊 Para conocer los detalles técnicos, metodología y resultados de esta investigación:</p>
              <a 
                href="https://www.canva.com/design/DAGrLYQZzQU/imyqzYwrZw4ylPYZFLrUzA/view?utm_content=DAGrLYQZzQU&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="poster-button"
              >
                Ver Póster Académico
              </a>
            </div>
          </div>
          <div className="footer-tech">
            <h4>Tecnologías Integradas</h4>
            <div className="tech-list">
              <span>OpenAI GPT-4o</span>
              <span>Claude 3.5 Sonnet</span>
              <span>Google Gemini 2.0</span>
              <span>DeepSeek R1</span>
              <span>RAG + Vector Store</span>
            </div>
          </div>
        </div>
      </footer>
      
      <Toaster 
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
        }}
      />
    </div>
  );
};

export default App; 