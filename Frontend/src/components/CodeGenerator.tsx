import React, { useState } from 'react';
import { CodeViewer } from './CodeViewer';
import { UMLDiagramEditor } from './UMLDiagramEditor';
import { ErrorMessage } from './ErrorMessage';

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
      const response = await fetch('http://localhost:8000/api/generate', {
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
        throw new Error('Failed to generate code');
      }

      const data = await response.json();
      setResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="code-generator">
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="userStory">User Story:</label>
          <textarea
            id="userStory"
            value={userStory}
            onChange={(e) => setUserStory(e.target.value)}
            placeholder="Enter your user story here..."
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="umlDiagram">UML Diagram:</label>
          <UMLDiagramEditor
            value={umlDiagram}
            onChange={setUmlDiagram}
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Generating...' : 'Generate Code'}
        </button>
      </form>

      {error && <ErrorMessage message={error} />}

      {response && (
        <div className="response-section">
          <h3>Generated Code</h3>
          <CodeViewer code={response.code} />

          <h3>Class Information</h3>
          <div className="class-info">
            {response.classInfo.map((classInfo, index) => (
              <div key={index} className="class-card">
                <h4>{classInfo.name}</h4>
                <p><strong>Purpose:</strong> {classInfo.purpose}</p>
                <div className="properties">
                  <h5>Properties:</h5>
                  <ul>
                    {classInfo.properties.map((prop, i) => (
                      <li key={i}>{prop}</li>
                    ))}
                  </ul>
                </div>
                <div className="methods">
                  <h5>Methods:</h5>
                  <ul>
                    {classInfo.methods.map((method, i) => (
                      <li key={i}>{method}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>

          <h3>Relationships</h3>
          <div className="relationships">
            {response.relationships.map((rel, index) => (
              <div key={index} className="relationship-card">
                <h4>{rel.from} → {rel.to}</h4>
                <p><strong>Type:</strong> {rel.type}</p>
                <p><strong>Description:</strong> {rel.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}; 