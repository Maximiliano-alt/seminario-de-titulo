import React from 'react';

interface LLMProvider {
  id: string;
  name: string;
  available: boolean;
}

interface LLMSelectorProps {
  availableLLMs: LLMProvider[];
  selectedLLM: string;
  onSelectLLM: (llmId: string) => void;
}

export const LLMSelector: React.FC<LLMSelectorProps> = ({
  availableLLMs,
  selectedLLM,
  onSelectLLM,
}) => {
  return (
    <div className="llm-selector">
      <label htmlFor="llm-select" className="control-label">
        Selección de Modelo de IA
      </label>
      <select
        id="llm-select"
        value={selectedLLM}
        onChange={(e) => onSelectLLM(e.target.value)}
        className="llm-select"
      >
        {availableLLMs.map((llm) => (
          <option key={llm.id} value={llm.id} disabled={!llm.available}>
            {llm.name} {!llm.available && '(No disponible)'}
          </option>
        ))}
      </select>
      <div className="llm-info">
        <p>Seleccionado: {availableLLMs.find(llm => llm.id === selectedLLM)?.name || 'Desconocido'}</p>
        <span className="llm-count">{availableLLMs.length} proveedores disponibles</span>
      </div>
    </div>
  );
}; 