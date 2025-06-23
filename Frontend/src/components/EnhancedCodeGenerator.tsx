import React, { useState, useEffect } from 'react';
import { LLMSelector } from './LLMSelector';
import { UserStoryInput } from './UserStoryInput';
import { DomainClassesView } from './DomainClassesView';
import { UMLPreview } from './UMLPreview';
import { JavaCodePreview } from './JavaCodePreview';
import { WorkflowStepper } from './WorkflowStepper';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorMessage } from './ErrorMessage';
import toast from 'react-hot-toast';
import { apiClient } from '../lib/api';
import { 
  Play, 
  Download, 
  Zap, 
  Code2, 
  FileText, 
  Workflow 
} from 'lucide-react';

// Types
interface DomainClass {
  name: string;
  purpose: string;
  fields: string[];
  methods: string[];
}

interface LLMProvider {
  id: string;
  name: string;
  available: boolean;
}

interface WorkflowStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'error';
}

interface CompleteWorkflowResponse {
  domain_classes: DomainClass[];
  plantuml_code: string;
  uml_image_base64?: string;
  uml_is_valid: boolean;
  uml_validation_message: string;
  java_classes?: Record<string, string>;
  project_structure?: Record<string, string[]>;
  dependencies?: string[];
  download_url?: string;
  llm_provider: string;
  total_classes: number;
  processing_time: number;
}

export const EnhancedCodeGenerator: React.FC = () => {
  // State management
  const [userStory, setUserStory] = useState('');
  const [selectedLLM, setSelectedLLM] = useState('gemini-2.0-flash-exp');
  const [availableLLMs, setAvailableLLMs] = useState<LLMProvider[]>([]);
  
  // Workflow state
  const [currentStep, setCurrentStep] = useState(0);
  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>([
    { id: 'input', title: 'Historia de Usuario', description: 'Definir requisitos', status: 'pending' },
    { id: 'domain', title: 'Análisis de Dominio', description: 'Extraer clases', status: 'pending' },
    { id: 'uml', title: 'Generación UML', description: 'Crear diagrama', status: 'pending' },
    { id: 'code', title: 'Generación de Código', description: 'Generar Java', status: 'pending' }
  ]);
  
  // Results state
  const [domainClasses, setDomainClasses] = useState<DomainClass[]>([]);
  const [plantumlCode, setPlantumlCode] = useState('');
  const [umlImageBase64, setUmlImageBase64] = useState<string | null>(null);
  const [javaClasses, setJavaClasses] = useState<Record<string, string>>({});
  const [projectStructure, setProjectStructure] = useState<Record<string, string[]>>({});
  const [dependencies, setDependencies] = useState<string[]>([]);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  
  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState<number | null>(null);

  // Load available LLMs on component mount
  useEffect(() => {
    loadAvailableLLMs();
  }, []);

  const loadAvailableLLMs = async () => {
    try {
      const data = await apiClient.get('/api/v2/llm-providers');
      
      const providers: LLMProvider[] = Object.entries(data.available_providers).map(([id, name]) => ({
        id,
        name: name as string,
        available: true
      }));
      
      setAvailableLLMs(providers);
      
      // Prioritize non-OpenAI providers to avoid quota issues
      const preferredProviders = ['gemini-2.0-flash-exp', 'claude-3-5-sonnet-20241022', 'deepseek-r1'];
      const availablePreferred = preferredProviders.find(id => providers.some(p => p.id === id));
      
      if (availablePreferred) {
        setSelectedLLM(availablePreferred);
      } else if (providers.length > 0 && !providers.find(p => p.id === selectedLLM)) {
        setSelectedLLM(providers[0].id);
      }
    } catch (err) {
      console.error('Failed to load LLM providers:', err);
      toast.error('Error al cargar los proveedores LLM disponibles');
    }
  };

  const updateWorkflowStep = (stepId: string, status: WorkflowStep['status']) => {
    setWorkflowSteps(prev => prev.map(step => 
      step.id === stepId ? { ...step, status } : step
    ));
  };

  const runCompleteWorkflow = async () => {
    if (!userStory.trim()) {
      toast.error('Por favor ingrese una historia de usuario');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      // Reset workflow
      setWorkflowSteps(prev => prev.map(step => ({ ...step, status: 'pending' })));
      setCurrentStep(0);

      // Mark input step as completed
      updateWorkflowStep('input', 'completed');
      setCurrentStep(1);

      // Start domain analysis
      updateWorkflowStep('domain', 'running');
      
      const result: CompleteWorkflowResponse = await apiClient.post('/api/v2/complete-workflow', {
        user_story: userStory,
        llm_provider: selectedLLM,
        include_java_code: true,
      });

      // Update domain analysis
      updateWorkflowStep('domain', 'completed');
      setDomainClasses(result.domain_classes);
      setCurrentStep(2);

      // Update UML generation
      updateWorkflowStep('uml', 'running');
      setPlantumlCode(result.plantuml_code);
      setUmlImageBase64(result.uml_image_base64 || null);
      updateWorkflowStep('uml', 'completed');
      setCurrentStep(3);

      // Update code generation
      updateWorkflowStep('code', 'running');
      setJavaClasses(result.java_classes || {});
      setProjectStructure(result.project_structure || {});
      setDependencies(result.dependencies || []);
      setDownloadUrl(result.download_url || null);
      updateWorkflowStep('code', 'completed');
      setCurrentStep(4);

      setProcessingTime(result.processing_time);
      
      toast.success(`Flujo completado en ${result.processing_time}s con ${result.total_classes} clases`);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Ocurrió un error';
      setError(errorMessage);
      toast.error(errorMessage);
      
      // Mark current step as error
      const currentStepId = workflowSteps[currentStep]?.id;
      if (currentStepId) {
        updateWorkflowStep(currentStepId, 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  const downloadProject = () => {
    if (downloadUrl) {
      window.open(apiClient.getDownloadUrl(downloadUrl), '_blank');
      toast.success('¡Descarga iniciada!');
    }
  };

  const resetWorkflow = () => {
    setUserStory('');
    setDomainClasses([]);
    setPlantumlCode('');
    setUmlImageBase64(null);
    setJavaClasses({});
    setProjectStructure({});
    setDependencies([]);
    setDownloadUrl(null);
    setError(null);
    setProcessingTime(null);
    setCurrentStep(0);
    setWorkflowSteps(prev => prev.map(step => ({ ...step, status: 'pending' })));
  };

  return (
    <div className="enhanced-code-generator">
      {/* Main Controls */}
      <div className="generator-controls">
        <div className="controls-header">
          <h2>
            <Workflow className="icon" />
            Pipeline de Generación
          </h2>
          <p>Transforme historias de usuario en Diagramas UML y código Java</p>
        </div>

        <div className="controls-grid">
          {/* LLM Selection */}
          <div className="control-group llm-selector-group">
            <LLMSelector
              availableLLMs={availableLLMs}
              selectedLLM={selectedLLM}
              onSelectLLM={setSelectedLLM}
            />
          </div>

          {/* User Story Input */}
          <div className="control-group user-story-group">
            <UserStoryInput
              value={userStory}
              onChange={setUserStory}
              isGenerating={loading}
            />
          </div>

          {/* Action Buttons */}
          <div className="control-group action-buttons-group">
            <div className="action-buttons">
              <button
                onClick={runCompleteWorkflow}
                disabled={loading || !userStory.trim()}
                className="btn btn-primary"
              >
                {loading ? (
                  <>
                    <LoadingSpinner size="sm" />
                    Procesando...
                  </>
                ) : (
                  <>
                    <Play className="icon" />
                    Ejecutar Pipeline
                  </>
                )}
              </button>

              <button
                onClick={resetWorkflow}
                disabled={loading}
                className="btn btn-secondary"
              >
                Reiniciar
              </button>

              {downloadUrl && (
                <button
                  onClick={downloadProject}
                  className="btn btn-success"
                >
                  <Download className="icon" />
                  Descargar Proyecto
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Workflow Progress */}
      <WorkflowStepper
        steps={workflowSteps}
        currentStep={currentStep}
        processingTime={processingTime}
      />

      {/* Error Display */}
      {error && <ErrorMessage message={error} />}

      {/* Results Section */}
      <div className="results-section">
        {/* Domain Classes */}
        {domainClasses.length > 0 && (
          <div className="result-card">
            <h3>
              <FileText className="icon" />
              Clases de Dominio ({domainClasses.length})
            </h3>
            <DomainClassesView classes={domainClasses} />
          </div>
        )}

        {/* UML Diagram */}
        {plantumlCode && (
          <div className="result-card">
            <h3>
              <Zap className="icon" />
              Diagrama de Clases UML
            </h3>
            <UMLPreview
              plantumlCode={plantumlCode}
              imageBase64={umlImageBase64}
            />
          </div>
        )}

        {/* Java Code */}
        {Object.keys(javaClasses).length > 0 && (
          <div className="result-card">
            <h3>
              <Code2 className="icon" />
              Código Java Generado ({Object.keys(javaClasses).length} archivos)
            </h3>
            <JavaCodePreview
              javaClasses={javaClasses}
              projectStructure={projectStructure}
              dependencies={dependencies}
              downloadUrl={downloadUrl}
            />
          </div>
        )}
      </div>
    </div>
  );
};