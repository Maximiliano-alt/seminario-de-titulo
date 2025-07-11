import os
import json
import logging
import tempfile
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling
)
from datasets import load_dataset, Dataset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class FineTuningConfig(BaseModel):
    """Configuration for fine-tuning an LLM"""
    base_model: str
    output_dir: str
    train_file: str
    validation_file: Optional[str] = None
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 8
    per_device_eval_batch_size: int = 8
    gradient_accumulation_steps: int = 1
    learning_rate: float = 5e-5
    weight_decay: float = 0.01
    warmup_steps: int = 500
    logging_steps: int = 100
    eval_steps: int = 500
    save_steps: int = 1000
    save_total_limit: int = 3
    max_seq_length: int = 512
    preprocessing_num_workers: int = 4
    push_to_hub: bool = False
    hub_model_id: Optional[str] = None
    hub_token: Optional[str] = None
    
class FineTuningDataProcessor:
    """Process data for fine-tuning an LLM"""
    
    def __init__(self, tokenizer, max_seq_length: int = 512):
        self.tokenizer = tokenizer
        self.max_seq_length = max_seq_length
        
    def prepare_user_story_to_java_dataset(self, examples: List[Dict[str, Any]]) -> Dataset:
        """
        Prepare a dataset for fine-tuning with user stories to Java code mapping
        
        Each example should have:
        - user_story: The user story text
        - uml_diagram: Optional UML diagram in PlantUML format
        - java_code: The Java code implementation
        """
        features = []
        
        for example in examples:
            # Format prompt
            prompt = f"USER STORY: {example['user_story']}\n\n"
            if 'uml_diagram' in example and example['uml_diagram']:
                prompt += f"UML DIAGRAM: {example['uml_diagram']}\n\n"
                
            prompt += "GENERATE JAVA CODE:\n\n"
            
            # Format completion
            completion = example['java_code']
            
            # Format as instruction fine-tuning example
            text = f"{prompt}{completion}</s>"
            
            # Tokenize
            tokenized = self.tokenizer(
                text,
                truncation=True,
                max_length=self.max_seq_length,
                padding="max_length"
            )
            
            features.append(tokenized)
            
        return Dataset.from_dict({k: [example[k] for example in features] for k in features[0].keys()})
    
    def prepare_ecommerce_dataset(self, json_file: str) -> Dict[str, Dataset]:
        """Prepare a dataset from a JSON file for eCommerce fine-tuning"""
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        examples = []
        
        for project in data:
            # Process each project into examples
            project_name = project.get('project_name', '')
            
            # Process user stories
            stories = project.get('stories', [])
            uml_diagrams = {uml.get('story_id'): uml.get('plantuml_code', '') 
                           for uml in project.get('uml', [])}
            
            classes_by_story = {}
            for story in stories:
                story_id = story.get('story_id', '')
                related_classes = story.get('related_classes', [])
                classes_by_story[story_id] = related_classes
                
            # Create examples from stories and related code
            for story in stories:
                story_id = story.get('story_id', '')
                uml_diagram = uml_diagrams.get(story_id, '')
                related_classes = classes_by_story.get(story_id, [])
                
                # Get code for related classes
                java_code = ""
                for class_name in related_classes:
                    for class_info in project.get('classes', []):
                        if class_info.get('file_name', '') == class_name:
                            java_code += f"// File: {class_name}\n"
                            java_code += class_info.get('content', '')
                            java_code += "\n\n"
                
                if java_code:
                    examples.append({
                        'user_story': story.get('description', ''),
                        'uml_diagram': uml_diagram,
                        'java_code': java_code
                    })
        
        # Split into train/validation
        train_size = int(len(examples) * 0.9)
        train_examples = examples[:train_size]
        eval_examples = examples[train_size:]
        
        # Create datasets
        train_dataset = self.prepare_user_story_to_java_dataset(train_examples)
        eval_dataset = self.prepare_user_story_to_java_dataset(eval_examples)
        
        return {
            'train': train_dataset,
            'validation': eval_dataset
        }

class LLMFineTuner:
    """Fine-tune an LLM for eCommerce Java code generation"""
    
    def __init__(self, config: FineTuningConfig):
        self.config = config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(config.base_model)
        self.model = AutoModelForCausalLM.from_pretrained(
            config.base_model,
            device_map="auto" if self.device == "cuda" else None
        )
        
        # Ensure the tokenizer has padding token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        # Create data processor
        self.data_processor = FineTuningDataProcessor(
            self.tokenizer,
            max_seq_length=config.max_seq_length
        )
        
    def prepare_dataset(self) -> Dict[str, Dataset]:
        """Prepare dataset for fine-tuning"""
        logger.info(f"Preparing datasets from {self.config.train_file}")
        return self.data_processor.prepare_ecommerce_dataset(self.config.train_file)
    
    def train(self, datasets: Optional[Dict[str, Dataset]] = None) -> None:
        """Train the model"""
        if not datasets:
            datasets = self.prepare_dataset()
            
        # Create data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        # Create training arguments
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_train_epochs,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            warmup_steps=self.config.warmup_steps,
            logging_steps=self.config.logging_steps,
            evaluation_strategy="steps",
            eval_steps=self.config.eval_steps,
            save_steps=self.config.save_steps,
            save_total_limit=self.config.save_total_limit,
            push_to_hub=self.config.push_to_hub,
            hub_model_id=self.config.hub_model_id,
            hub_token=self.config.hub_token,
            fp16=self.device == "cuda"
        )
        
        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=datasets['train'],
            eval_dataset=datasets['validation'],
            data_collator=data_collator,
            tokenizer=self.tokenizer
        )
        
        # Train
        logger.info("Starting training...")
        trainer.train()
        
        # Save model
        logger.info(f"Saving model to {self.config.output_dir}")
        trainer.save_model()
        self.tokenizer.save_pretrained(self.config.output_dir)
        
        return trainer
        
def fine_tune_model(dataset_path: str, base_model: str = "gpt2", output_dir: str = None):
    """Fine-tune a model for eCommerce Java code generation"""
    if not output_dir:
        output_dir = os.path.join(tempfile.gettempdir(), "ecommerce-java-model")
        
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create configuration
    config = FineTuningConfig(
        base_model=base_model,
        output_dir=output_dir,
        train_file=dataset_path,
        num_train_epochs=3,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4
    )
    
    # Initialize fine-tuner
    fine_tuner = LLMFineTuner(config)
    
    # Train model
    trainer = fine_tuner.train()
    
    return {
        "status": "success",
        "message": f"Model fine-tuned and saved to {output_dir}",
        "model_path": output_dir
    }

if __name__ == "__main__":
    # Example usage
    dataset_path = "../data/dataset_new.json"
    result = fine_tune_model(dataset_path, base_model="gpt2")
    print(result) 