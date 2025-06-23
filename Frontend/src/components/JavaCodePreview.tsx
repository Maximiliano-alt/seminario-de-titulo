import React, { useState } from 'react';
import { Download, Copy, Package, FileCode, Layers } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '../lib/api';

interface JavaCodePreviewProps {
  javaClasses: Record<string, string>;
  projectStructure: Record<string, string[]>;
  dependencies: string[];
  downloadUrl?: string | null;
}

export const JavaCodePreview: React.FC<JavaCodePreviewProps> = ({
  javaClasses,
  projectStructure,
  dependencies,
  downloadUrl,
}) => {
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'code' | 'structure' | 'dependencies'>('code');

  const fileNames = Object.keys(javaClasses);

  React.useEffect(() => {
    if (fileNames.length > 0 && !selectedFile) {
      setSelectedFile(fileNames[0]);
    }
  }, [fileNames, selectedFile]);

  const copyToClipboard = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      toast.success('¡Código copiado al portapapeles!');
    } catch (err) {
      console.error('Failed to copy: ', err);
      toast.error('Error al copiar código al portapapeles');
    }
  };

  const copyAllFiles = async () => {
    try {
      const allCode = Object.entries(javaClasses)
        .map(([fileName, code]) => `// ========== ${fileName} ==========\n${code}`)
        .join('\n\n');
      
      await navigator.clipboard.writeText(allCode);
      toast.success(`¡Todos los ${fileNames.length} archivos copiados al portapapeles!`);
    } catch (err) {
      console.error('Failed to copy all files: ', err);
      toast.error('Error al copiar todos los archivos al portapapeles');
    }
  };

  const downloadProject = () => {
    if (downloadUrl) {
      window.open(apiClient.getDownloadUrl(downloadUrl), '_blank');
      toast.success('¡Descarga iniciada!');
    } else {
      toast.error('URL de descarga no disponible');
    }
  };

  const createClientSideZip = async () => {
    // Fallback to server download for now
    if (downloadUrl) {
      downloadProject();
    } else {
      toast.error('Funcionalidad de descarga no disponible. Use la descarga del servidor.');
    }
  };

  return (
    <div className="java-code-preview">
      {/* Header with action buttons */}
      <div className="preview-header">
        <div className="preview-tabs">
          <button
            className={`tab ${activeTab === 'code' ? 'active' : ''}`}
            onClick={() => setActiveTab('code')}
          >
            <FileCode className="icon" />
            Código Generado
          </button>
          <button
            className={`tab ${activeTab === 'structure' ? 'active' : ''}`}
            onClick={() => setActiveTab('structure')}
          >
            <Package className="icon" />
            Estructura del Proyecto
          </button>
          <button
            className={`tab ${activeTab === 'dependencies' ? 'active' : ''}`}
            onClick={() => setActiveTab('dependencies')}
          >
            <Layers className="icon" />
            Dependencias
          </button>
        </div>

        <div className="header-actions">
          <button 
            className="action-btn copy-all-btn"
            onClick={copyAllFiles}
            title="Copiar todos los archivos al portapapeles"
          >
            <Copy className="icon" />
            Copiar Todo
          </button>
          
          {downloadUrl ? (
            <button 
              className="action-btn download-btn primary"
              onClick={downloadProject}
              title="Descargar proyecto completo como ZIP"
            >
              <Download className="icon" />
              Descargar ZIP
            </button>
          ) : (
            <button 
              className="action-btn download-btn primary"
              onClick={createClientSideZip}
              title="Crear y descargar archivo ZIP"
            >
              <Download className="icon" />
              Descargar ZIP
            </button>
          )}
        </div>
      </div>

      <div className="preview-content">
        {activeTab === 'code' && (
          <div className="code-section">
            <div className="file-selector">
              <h4>Seleccionar Archivo:</h4>
              <select
                value={selectedFile}
                onChange={(e) => setSelectedFile(e.target.value)}
                className="file-select"
              >
                {fileNames.map((fileName) => (
                  <option key={fileName} value={fileName}>
                    {fileName}
                  </option>
                ))}
              </select>
              {selectedFile && (
                <button 
                  className="copy-btn"
                  onClick={() => copyToClipboard(javaClasses[selectedFile])}
                >
                  <Copy className="icon-sm" />
                  Copiar Código
                </button>
              )}
            </div>

            {selectedFile && (
              <div className="code-display">
                <div className="code-header">
                  <span className="file-name">{selectedFile}</span>
                  <span className="file-size">
                    {javaClasses[selectedFile].split('\n').length} líneas
                  </span>
                </div>
                <pre className="java-code">
                  <code>{javaClasses[selectedFile]}</code>
                </pre>
              </div>
            )}
          </div>
        )}

        {activeTab === 'structure' && (
          <div className="structure-section">
            <h4>Estructura del Proyecto:</h4>
            <div className="structure-tree">
              {Object.entries(projectStructure).map(([packageName, classes]) => (
                <div key={packageName} className="package-group">
                  <div className="package-name">
                    <Package className="icon-sm" />
                    {packageName}
                  </div>
                  <div className="package-classes">
                    {classes.map((className) => (
                      <div key={className} className="class-file">
                        <FileCode className="icon-sm" />
                        {className}.java
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'dependencies' && (
          <div className="dependencies-section">
            <h4>Dependencias del Proyecto:</h4>
            <div className="dependencies-list">
              {dependencies.map((dependency, index) => (
                <div key={index} className="dependency-item">
                  <span className="dependency-icon">📚</span>
                  <span className="dependency-name">{dependency}</span>
                </div>
              ))}
            </div>
            <div className="tech-stack">
              <h5>Stack Tecnológico:</h5>
              <div className="tech-badges">
                <span className="tech-badge">Spring Boot</span>
                <span className="tech-badge">Java 17+</span>
                <span className="tech-badge">Maven</span>
                <span className="tech-badge">JPA/Hibernate</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="preview-info">
        <p>
          <strong>Archivos:</strong> {fileNames.length} | 
          <strong> Paquetes:</strong> {Object.keys(projectStructure).length} |
          <strong> Dependencias:</strong> {dependencies.length}
        </p>
      </div>
    </div>
  );
}; 