import React, { useState, useEffect } from 'react';

interface UMLPreviewProps {
  plantumlCode: string;
  imageBase64?: string | null;
}

export const UMLPreview: React.FC<UMLPreviewProps> = ({ plantumlCode, imageBase64 }) => {
  const [activeTab, setActiveTab] = useState<'diagram' | 'code'>('diagram');
  const [diagramUrl, setDiagramUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generate diagram when plantumlCode changes
  useEffect(() => {
    const renderDiagram = async () => {
      console.log('UMLPreview: plantumlCode changed:', plantumlCode);
      
      if (plantumlCode && plantumlCode.trim()) {
        console.log('UMLPreview: Starting diagram rendering...');
        setIsLoading(true);
        setError(null);
        
        try {
          const apiBaseUrl = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000';
          console.log('UMLPreview: API Base URL:', apiBaseUrl);
          
          const response = await fetch(`${apiBaseUrl}/api/v2/render-uml`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              plantuml_code: plantumlCode
            })
          });
          
          console.log('UMLPreview: Response status:', response.status);
          const result = await response.json();
          console.log('UMLPreview: Response result:', result);
          
          if (result.success && result.image_base64) {
            console.log('UMLPreview: Setting diagram URL');
            setDiagramUrl(`data:image/png;base64,${result.image_base64}`);
          } else {
            console.error('UMLPreview: Failed to render:', result.error);
            setError(result.error || 'Error al renderizar diagrama');
          }
        } catch (err) {
          console.error('Error rendering diagram:', err);
          setError('Error al conectar con el servicio de renderizado');
        } finally {
          setIsLoading(false);
        }
      } else {
        console.log('UMLPreview: No PlantUML code provided');
      }
    };
    
    renderDiagram();
  }, [plantumlCode]);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(plantumlCode);
      alert('¡Código PlantUML copiado al portapapeles!');
    } catch (err) {
      console.error('Failed to copy: ', err);
    }
  };

  return (
    <div className="uml-preview">
      <div className="uml-tabs">
        <button
          className={`tab ${activeTab === 'diagram' ? 'active' : ''}`}
          onClick={() => setActiveTab('diagram')}
        >
          Diagrama
        </button>
        <button
          className={`tab ${activeTab === 'code' ? 'active' : ''}`}
          onClick={() => setActiveTab('code')}
        >
          Código PlantUML
        </button>
        <button className="copy-btn" onClick={copyToClipboard}>
          Copiar Código
        </button>
      </div>

      <div className="uml-content">
        {activeTab === 'diagram' && (
          <div className="uml-diagram">
            {isLoading ? (
              <div className="diagram-loading">
                <p>Generando diagrama UML...</p>
                <div className="loading-spinner"></div>
              </div>
            ) : error ? (
              <div className="diagram-error">
                <p>Error: {error}</p>
                <p>Cambie a la pestaña "Código PlantUML" para ver el código generado</p>
              </div>
            ) : diagramUrl ? (
              <div className="diagram-container">
                <img 
                  src={diagramUrl} 
                  alt="Diagrama de Clases UML"
                  className="uml-image"
                  onError={() => setError('Error al cargar diagrama desde servidor PlantUML')}
                  onLoad={() => setError(null)}
                />
                <p className="diagram-info">Diagrama de Clases UML renderizado vía servidor PlantUML</p>
              </div>
            ) : imageBase64 ? (
              <div className="diagram-container">
                <img 
                  src={`data:image/png;base64,${imageBase64}`} 
                  alt="Diagrama de Clases UML"
                  className="uml-image"
                />
                <p className="diagram-info">Diagrama de Clases UML generado exitosamente</p>
              </div>
            ) : (
              <div className="diagram-placeholder">
                <p>Vista previa del diagrama UML no disponible</p>
                <p>Cambie a la pestaña "Código PlantUML" para ver el código generado</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'code' && (
          <div className="uml-code">
            <pre className="plantuml-code">
              <code>{plantumlCode}</code>
            </pre>
          </div>
        )}
      </div>

      <div className="uml-info">
        <p>
          <strong>Líneas:</strong> {plantumlCode.split('\n').length} | 
          <strong> Caracteres:</strong> {plantumlCode.length}
        </p>
      </div>
    </div>
  );
}; 