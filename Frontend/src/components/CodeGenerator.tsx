import React, { useState } from 'react';
import { CodeViewer } from './CodeViewer';
import { UMLDiagramEditor } from './UMLDiagramEditor';
import { ErrorMessage } from './ErrorMessage';
import { API_BASE_URL } from '../lib/api';

interface ClassInfo {
  name: string;
  purpose: string;
  properties: string[];
  methods: string[];
}

interface Relationship {
  from: string;
  to: string;
  type: string;
  description: string;
}

interface GenerationResponse {
  code: string;
  classInfo: ClassInfo[];
  relationships: Relationship[];
}

export const CodeGenerator: React.FC = () => {
  const [userStory, setUserStory] = useState('');
  const [umlDiagram, setUmlDiagram] = useState('');
  const [response, setResponse] = useState<GenerationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(API_BASE_URL + '/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userStory,
          umlDiagram,
        }),
      });

      if (!response.ok) {
        throw new Error('Error al generar código');
      }

      const data = await response.json();
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ocurrió un error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="code-generator">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="userStory">Historia de Usuario:</label>
          <textarea
            id="userStory"
            value={userStory}
            onChange={(e) => setUserStory(e.target.value)}
            placeholder="Ingrese su historia de usuario aquí..."
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="umlDiagram">Diagrama UML:</label>
          <UMLDiagramEditor
            value={umlDiagram}
            onChange={setUmlDiagram}
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Generando...' : 'Generar Código'}
        </button>
      </form>

      {error && <ErrorMessage message={error} />}

      {response && (
        <div className="response-section">
          <h3>Código Generado</h3>
          <CodeViewer code={response.code} />

          <h3>Información de Clases</h3>
          <div className="class-info">
            {response.classInfo.map((classInfo, index) => (
              <div key={index} className="class-card">
                <h4>{classInfo.name}</h4>
                <p><strong>Propósito:</strong> {classInfo.purpose}</p>
                <div className="properties">
                  <h5>Propiedades:</h5>
                  <ul>
                    {classInfo.properties.map((prop, i) => (
                      <li key={i}>{prop}</li>
                    ))}
                  </ul>
                </div>
                <div className="methods">
                  <h5>Métodos:</h5>
                  <ul>
                    {classInfo.methods.map((method, i) => (
                      <li key={i}>{method}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>

          <h3>Relaciones</h3>
          <div className="relationships">
            {response.relationships.map((rel, index) => (
              <div key={index} className="relationship-card">
                <h4>{rel.from} → {rel.to}</h4>
                <p><strong>Tipo:</strong> {rel.type}</p>
                <p><strong>Descripción:</strong> {rel.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}; 