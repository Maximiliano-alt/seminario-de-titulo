# Code Generation Demo

This demo showcases the LLM-based code generation system that translates user stories and UML diagrams into working code.

## Features

- Input user stories in a structured format
- Provide UML diagrams in PlantUML syntax
- Generate code based on both inputs using a trained LLM
- Copy generated code to clipboard with one click

## Technologies Used

- **Frontend**: React, TypeScript, Vite
- **Backend**: FastAPI, Python
- **LLM Integration**: LangChain with OpenAI

## Setup Instructions

### Prerequisites

- Node.js (v14+)
- Python 3.8+
- OpenAI API key (set in .env file)

### Installation

1. Clone the repository
2. Install dependencies:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd Frontend
npm install
```

3. Create a `.env` file in the root directory with your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

### Running the Demo

You can run both the frontend and backend with a single command:

```bash
./run.sh
```

Or run them separately:

#### Backend

```bash
cd Backend
python api.py
```

#### Frontend

```bash
cd Frontend
npm run dev
```

## Usage Guide

1. Enter a user story in the first text area
2. Provide a UML class diagram in PlantUML syntax in the second text area
3. Click "Generate Code"
4. View the generated code and copy it to your clipboard if desired

## Example Inputs

### User Story Example

```
As a customer, I want to be able to add items to my shopping cart so that I can purchase them later.
```

### UML Diagram Example

```
@startuml
class ShoppingCart {
  -items: List<Item>
  +addItem(item: Item): void
  +removeItem(itemId: String): void
  +getTotal(): double
}

class Item {
  -id: String
  -name: String
  -price: double
  +getId(): String
  +getName(): String
  +getPrice(): double
}
@enduml
```
