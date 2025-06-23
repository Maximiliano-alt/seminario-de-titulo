import React from 'react';

interface DomainClass {
  name: string;
  purpose: string;
  fields: string[];
  methods: string[];
}

interface DomainClassesViewProps {
  classes: DomainClass[];
}

export const DomainClassesView: React.FC<DomainClassesViewProps> = ({ classes }) => {
  return (
    <div className="domain-classes-view">
      <div className="classes-grid">
        {classes.map((domainClass, index) => (
          <div key={index} className="class-card">
            <div className="class-header">
              <h4 className="class-name">{domainClass.name}</h4>
              <span className="class-index">#{index + 1}</span>
            </div>
            
            <div className="class-purpose">
              <p>{domainClass.purpose}</p>
            </div>
            
            <div className="class-details">
              <div className="class-section">
                <h5>Campos ({domainClass.fields.length})</h5>
                <ul className="fields-list">
                  {domainClass.fields.map((field, fieldIndex) => (
                    <li key={fieldIndex} className="field-item">
                      <code>{field}</code>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="class-section">
                <h5>Métodos ({domainClass.methods.length})</h5>
                <ul className="methods-list">
                  {domainClass.methods.map((method, methodIndex) => (
                    <li key={methodIndex} className="method-item">
                      <code>{method}</code>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="classes-summary">
        <p>
          <strong>Resumen del Análisis de Dominio:</strong> Se identificaron {classes.length} clases principales 
          con un total de {classes.reduce((sum, c) => sum + c.fields.length, 0)} campos 
          y {classes.reduce((sum, c) => sum + c.methods.length, 0)} métodos.
        </p>
      </div>
    </div>
  );
}; 