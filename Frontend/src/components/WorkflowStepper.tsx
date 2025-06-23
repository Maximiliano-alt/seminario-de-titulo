import React from 'react';

interface WorkflowStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'error';
}

interface WorkflowStepperProps {
  steps: WorkflowStep[];
  currentStep: number;
  processingTime?: number | null;
}

export const WorkflowStepper: React.FC<WorkflowStepperProps> = ({
  steps,
  currentStep,
  processingTime,
}) => {
  return (
    <div className="workflow-progress">
      <h3>Progreso del Flujo de Trabajo</h3>
      
      <div className="steps-container">
        {steps.map((step, index) => (
          <div key={step.id} className={`step ${step.status}`}>
            <div className="step-indicator">
              {step.status === 'completed' ? '✓' : index + 1}
            </div>
            <div className="step-content">
              <div className="step-title">{step.title}</div>
              <div className="step-description">{step.description}</div>
            </div>
          </div>
        ))}
      </div>
      
      {processingTime && (
        <div className="processing-info">
          <p>Procesamiento completado en {processingTime}s</p>
        </div>
      )}
    </div>
  );
}; 