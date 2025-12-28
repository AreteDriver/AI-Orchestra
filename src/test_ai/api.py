"""FastAPI backend for AI Workflow Orchestrator."""
from datetime import datetime
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

from test_ai.auth import create_access_token, verify_token
from test_ai.orchestrator import WorkflowEngine, Workflow
from test_ai.prompts import PromptTemplateManager, PromptTemplate
from test_ai.api_clients import OpenAIClient

app = FastAPI(title="AI Workflow Orchestrator", version="0.1.0")

# Initialize components
workflow_engine = WorkflowEngine()
prompt_manager = PromptTemplateManager()
openai_client = OpenAIClient()


class LoginRequest(BaseModel):
    """Login request."""
    user_id: str
    password: str


class LoginResponse(BaseModel):
    """Login response."""
    access_token: str
    token_type: str = "bearer"


class WorkflowExecuteRequest(BaseModel):
    """Request to execute a workflow."""
    workflow_id: str
    variables: Optional[Dict] = None


def verify_auth(authorization: Optional[str] = Header(None)) -> str:
    """Verify authentication token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    user_id = verify_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user_id


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "app": "AI Workflow Orchestrator",
        "version": "0.1.0",
        "status": "running"
    }


@app.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """Login endpoint (simplified)."""
    if request.password == "demo":
        token = create_access_token(request.user_id)
        return LoginResponse(access_token=token)
    
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/workflows")
def list_workflows(authorization: Optional[str] = Header(None)):
    """List all workflows."""
    verify_auth(authorization)
    return workflow_engine.list_workflows()


@app.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: str, authorization: Optional[str] = Header(None)):
    """Get a specific workflow."""
    verify_auth(authorization)
    workflow = workflow_engine.load_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow


@app.post("/workflows")
def create_workflow(workflow: Workflow, authorization: Optional[str] = Header(None)):
    """Create a new workflow."""
    verify_auth(authorization)
    
    if workflow_engine.save_workflow(workflow):
        return {"status": "success", "workflow_id": workflow.id}
    
    raise HTTPException(status_code=500, detail="Failed to save workflow")


@app.post("/workflows/execute")
def execute_workflow(request: WorkflowExecuteRequest, authorization: Optional[str] = Header(None)):
    """Execute a workflow."""
    verify_auth(authorization)
    
    workflow = workflow_engine.load_workflow(request.workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if request.variables:
        workflow.variables.update(request.variables)
    
    result = workflow_engine.execute_workflow(workflow)
    return result


@app.get("/prompts")
def list_prompts(authorization: Optional[str] = Header(None)):
    """List all prompt templates."""
    verify_auth(authorization)
    return prompt_manager.list_templates()


@app.get("/prompts/{template_id}")
def get_prompt(template_id: str, authorization: Optional[str] = Header(None)):
    """Get a specific prompt template."""
    verify_auth(authorization)
    template = prompt_manager.load_template(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@app.post("/prompts")
def create_prompt(template: PromptTemplate, authorization: Optional[str] = Header(None)):
    """Create a new prompt template."""
    verify_auth(authorization)
    
    if prompt_manager.save_template(template):
        return {"status": "success", "template_id": template.id}
    
    raise HTTPException(status_code=500, detail="Failed to save template")


@app.delete("/prompts/{template_id}")
def delete_prompt(template_id: str, authorization: Optional[str] = Header(None)):
    """Delete a prompt template."""
    verify_auth(authorization)
    
    if prompt_manager.delete_template(template_id):
        return {"status": "success"}
    
    raise HTTPException(status_code=404, detail="Template not found")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
