"""
Project Manager - Multi-step project handling with automatic progression.
Manages complex projects that require multiple steps to complete.
"""

import logging
import json
import os
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from models.code_request import CodeRequest
from models.code_response import CodeResponse
from config.constants import PromptType


logger = logging.getLogger(__name__)


class ProjectStage(Enum):
    """Project stages for multi-step execution."""
    PLANNING = "planning"
    ANALYSIS = "analysis"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"
    COMPLETED = "completed"


@dataclass
class ProjectStep:
    """Individual step in a project."""
    id: str
    title: str
    description: str
    stage: ProjectStage
    dependencies: List[str] = field(default_factory=list)
    estimated_time: int = 0  # minutes
    priority: int = 1  # 1=high, 5=low
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[CodeResponse] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'stage': self.stage.value,
            'dependencies': self.dependencies,
            'estimated_time': self.estimated_time,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class Project:
    """Multi-step project with automatic progression."""
    id: str
    name: str
    description: str
    steps: List[ProjectStep] = field(default_factory=list)
    current_step: Optional[str] = None
    auto_progression: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'steps': [step.to_dict() for step in self.steps],
            'current_step': self.current_step,
            'auto_progression': self.auto_progression,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }


class ProjectManager:
    """
    Project Manager - Handles multi-step project execution.
    
    Features:
    - Automatic project breakdown
    - Step-by-step execution
    - Dependency management
    - Progress tracking
    - Auto-progression
    """
    
    def __init__(self, engine, storage_path: str = "projects"):
        """Initialize project manager."""
        self.engine = engine
        self.storage_path = storage_path
        self.active_projects: Dict[str, Project] = {}
        
        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)
        
        logger.info("Project manager initialized")
    
    def create_project(self, name: str, description: str, auto_breakdown: bool = True) -> str:
        """Create a new multi-step project."""
        try:
            project_id = f"project_{int(time.time())}"
            
            project = Project(
                id=project_id,
                name=name,
                description=description,
                auto_progression=True
            )
            
            # Automatic project breakdown
            if auto_breakdown:
                self._breakdown_project(project)
            
            # Store project
            self.active_projects[project_id] = project
            self._save_project(project)
            
            logger.info(f"Created project: {name} ({project_id})")
            return project_id
            
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise
    
    def execute_project(self, project_id: str) -> Dict[str, Any]:
        """Execute project step by step."""
        try:
            if project_id not in self.active_projects:
                raise ValueError(f"Project {project_id} not found")
            
            project = self.active_projects[project_id]
            results = []
            
            logger.info(f"Starting project execution: {project.name}")
            
            while True:
                # Get next executable step
                next_step = self._get_next_step(project)
                if not next_step:
                    break
                
                # Execute step
                result = self._execute_step(project, next_step)
                results.append({
                    'step': next_step.title,
                    'result': result,
                    'status': next_step.status
                })
                
                # Update project state
                self._save_project(project)
                
                # Check if auto-progression should continue
                if not project.auto_progression or next_step.status == "failed":
                    break
            
            # Mark project as completed if all steps are done
            if self._is_project_complete(project):
                logger.info(f"Project completed: {project.name}")
            
            return {
                'project_id': project_id,
                'project_name': project.name,
                'total_steps': len(project.steps),
                'completed_steps': len([s for s in project.steps if s.status == "completed"]),
                'results': results,
                'status': 'completed' if self._is_project_complete(project) else 'in_progress'
            }
            
        except Exception as e:
            logger.error(f"Project execution failed: {e}")
            raise
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get current project status."""
        if project_id not in self.active_projects:
            return {'error': 'Project not found'}
        
        project = self.active_projects[project_id]
        
        completed_steps = [s for s in project.steps if s.status == "completed"]
        pending_steps = [s for s in project.steps if s.status == "pending"]
        
        return {
            'project_id': project_id,
            'name': project.name,
            'description': project.description,
            'total_steps': len(project.steps),
            'completed_steps': len(completed_steps),
            'pending_steps': len(pending_steps),
            'current_step': project.current_step,
            'progress_percent': (len(completed_steps) / len(project.steps)) * 100 if project.steps else 0,
            'is_complete': self._is_project_complete(project),
            'steps': [step.to_dict() for step in project.steps]
        }
    
    def _breakdown_project(self, project: Project):
        """Automatically breakdown project into steps."""
        try:
            # Create breakdown request
            breakdown_prompt = f"""
            Analyze this project and create a detailed step-by-step breakdown:
            
            PROJECT: {project.name}
            DESCRIPTION: {project.description}
            
            Create a comprehensive project plan with the following stages:
            1. PLANNING - Requirements analysis, architecture planning
            2. DESIGN - System design, UI/UX design, database design
            3. IMPLEMENTATION - Core development, feature implementation
            4. TESTING - Unit tests, integration tests, user testing
            5. OPTIMIZATION - Performance optimization, code cleanup
            6. DOCUMENTATION - Code documentation, user guides
            
            For each step, provide:
            - Clear title and description
            - Dependencies (which steps must be completed first)
            - Estimated time in minutes
            - Priority level (1-5)
            - Specific implementation details
            
            Format as JSON with steps array.
            """
            
            request = CodeRequest(
                description=breakdown_prompt,
                prompt_type=PromptType.TASK_DECOMPOSITION,
                language="json"
            )
            
            response = self.engine.generate_code(request)
            
            if response.success:
                # Parse the breakdown response
                self._parse_breakdown_response(project, response.content)
            else:
                # Create default steps if breakdown fails
                self._create_default_steps(project)
                
        except Exception as e:
            logger.error(f"Project breakdown failed: {e}")
            self._create_default_steps(project)
    
    def _parse_breakdown_response(self, project: Project, content: str):
        """Parse AI breakdown response into project steps."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_content = content[json_start:json_end].strip()
            else:
                json_content = content
            
            breakdown_data = json.loads(json_content)
            
            if 'steps' in breakdown_data:
                for i, step_data in enumerate(breakdown_data['steps']):
                    step = ProjectStep(
                        id=f"step_{i+1}",
                        title=step_data.get('title', f'Step {i+1}'),
                        description=step_data.get('description', ''),
                        stage=ProjectStage(step_data.get('stage', 'implementation')),
                        dependencies=step_data.get('dependencies', []),
                        estimated_time=step_data.get('estimated_time', 30),
                        priority=step_data.get('priority', 3)
                    )
                    project.steps.append(step)
            
            logger.info(f"Created {len(project.steps)} steps for project {project.name}")
            
        except Exception as e:
            logger.error(f"Failed to parse breakdown response: {e}")
            self._create_default_steps(project)
    
    def _create_default_steps(self, project: Project):
        """Create default steps if breakdown fails."""
        default_steps = [
            ("Planning", "Analyze requirements and plan architecture", ProjectStage.PLANNING),
            ("Design", "Create system design and specifications", ProjectStage.DESIGN),
            ("Implementation", "Implement core functionality", ProjectStage.IMPLEMENTATION),
            ("Testing", "Create and run tests", ProjectStage.TESTING),
            ("Documentation", "Create documentation", ProjectStage.DOCUMENTATION)
        ]
        
        for i, (title, desc, stage) in enumerate(default_steps):
            step = ProjectStep(
                id=f"step_{i+1}",
                title=title,
                description=desc,
                stage=stage,
                estimated_time=60,
                priority=i+1
            )
            project.steps.append(step)
    
    def _get_next_step(self, project: Project) -> Optional[ProjectStep]:
        """Get the next executable step."""
        for step in project.steps:
            if step.status == "pending" and self._are_dependencies_met(project, step):
                return step
        return None
    
    def _are_dependencies_met(self, project: Project, step: ProjectStep) -> bool:
        """Check if step dependencies are satisfied."""
        for dep_id in step.dependencies:
            dep_step = next((s for s in project.steps if s.id == dep_id), None)
            if not dep_step or dep_step.status != "completed":
                return False
        return True
    
    def _execute_step(self, project: Project, step: ProjectStep) -> CodeResponse:
        """Execute a single project step."""
        try:
            step.status = "in_progress"
            project.current_step = step.id
            
            logger.info(f"Executing step: {step.title}")
            
            # Create step execution prompt
            step_prompt = f"""
            Execute this project step:
            
            PROJECT: {project.name}
            CURRENT STEP: {step.title}
            DESCRIPTION: {step.description}
            STAGE: {step.stage.value}
            
            Previous completed steps context:
            {self._get_completed_steps_context(project)}
            
            Provide detailed implementation for this step including:
            - Code implementation (if applicable)
            - Configuration files
            - Documentation
            - Test cases (if applicable)
            
            Focus on {step.stage.value} stage requirements.
            """
            
            request = CodeRequest(
                description=step_prompt,
                prompt_type=PromptType.GENERATE,
                language="auto-detect"
            )
            
            response = self.engine.generate_code(request)
            
            if response.success:
                step.status = "completed"
                step.result = response
                
                # Save generated code if any
                if response.code_blocks:
                    self._save_step_artifacts(project, step, response.code_blocks)
                
                logger.info(f"Step completed: {step.title}")
            else:
                step.status = "failed"
                logger.error(f"Step failed: {step.title}")
            
            return response
            
        except Exception as e:
            step.status = "failed"
            logger.error(f"Step execution error: {e}")
            raise
    
    def _get_completed_steps_context(self, project: Project) -> str:
        """Get context from completed steps."""
        completed_steps = [s for s in project.steps if s.status == "completed"]
        context_parts = []
        
        for step in completed_steps[-3:]:  # Last 3 completed steps
            if step.result and step.result.content:
                context_parts.append(f"Step: {step.title}\nResult: {step.result.content[:500]}...")
        
        return "\n\n".join(context_parts)
    
    def _save_step_artifacts(self, project: Project, step: ProjectStep, code_blocks):
        """Save step artifacts to project directory."""
        try:
            project_dir = os.path.join(self.storage_path, project.id)
            step_dir = os.path.join(project_dir, f"step_{step.id}")
            os.makedirs(step_dir, exist_ok=True)
            
            for i, block in enumerate(code_blocks):
                filename = f"{step.id}_{block.language.value}_{i+1}.{block.language.value}"
                filepath = os.path.join(step_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(block.code)
                
                logger.info(f"Saved artifact: {filepath}")
                
        except Exception as e:
            logger.error(f"Failed to save step artifacts: {e}")
    
    def _is_project_complete(self, project: Project) -> bool:
        """Check if project is complete."""
        return all(step.status == "completed" for step in project.steps)
    
    def _save_project(self, project: Project):
        """Save project to storage."""
        try:
            project_file = os.path.join(self.storage_path, f"{project.id}.json")
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project.to_dict(), f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save project: {e}")
    
    def load_project(self, project_id: str) -> Optional[Project]:
        """Load project from storage."""
        try:
            project_file = os.path.join(self.storage_path, f"{project_id}.json")
            if os.path.exists(project_file):
                with open(project_file, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                # TODO: Implement proper deserialization
                return None  # Placeholder
            return None
            
        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            return None 