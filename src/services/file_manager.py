"""
File management service for saving and organizing generated code.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from config.settings import Settings
from config.constants import FILE_EXTENSIONS, CodeLanguage
from models.code_response import CodeBlock


logger = logging.getLogger(__name__)


class FileManagerService:
    """Service for managing generated code files."""
    
    def __init__(self, settings: Settings):
        """Initialize file manager service."""
        self.settings = settings
        self.base_output_dir = Path(settings.output_directory)
        self.base_output_dir.mkdir(exist_ok=True)
    
    def save_code_blocks(
    self, 
    code_blocks: List[CodeBlock], 
    project_name: str, 
    timestamp: Optional[str] = None,
    ) -> List[str]:
        """Save code blocks to organized file structure."""
        if not timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        project_dir = self.base_output_dir / f"{project_name}_{timestamp}"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        
        # Group blocks by language for better organization
        language_groups = self._group_blocks_by_language(code_blocks)
        
        for language, blocks in language_groups.items():
            # Create language-specific subdirectory if multiple languages
            if len(language_groups) > 1:
                lang_dir = project_dir / language.value
                lang_dir.mkdir(exist_ok=True)
            else:
                lang_dir = project_dir
            
            for i, block in enumerate(blocks):
                file_path = self._generate_file_path(lang_dir, block, i)
                self._write_code_file(file_path, block)
                saved_files.append(str(file_path))
        
        # Create project metadata
        self._create_project_metadata(project_dir, project_name, code_blocks)
        
        logger.info(f"Saved {len(saved_files)} files to {project_dir}")
        return saved_files
    
    def save_single_file(
        self,
        code: str, 
        filename: str, 
        language: CodeLanguage,
        project_name: Optional[str] = None,
    ) -> str:
        """Save a single code file."""

        if project_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.base_output_dir / f"{project_name}_{timestamp}"
        else:
            output_dir = self.base_output_dir / "single_files"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        extension = FILE_EXTENSIONS.get(language.value, ".txt")
        if not filename.endswith(extension): filename = f"{filename}{extension}"
        
        file_path = output_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        logger.info(f"Saved single file: {file_path}")
        return str(file_path)
    
    def create_project_structure(
        self, 
        project_name: str, 
        structure: Dict[str, Any],
    ) -> str:
        """Create a complete project structure from specification."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_dir = self.base_output_dir / f"{project_name}_{timestamp}"
        
        self._create_directory_structure(project_dir, structure)
        
        logger.info(f"Created project structure: {project_dir}")
        return str(project_dir)
    
    def _group_blocks_by_language(
        self, 
        code_blocks: List[CodeBlock]
    ) -> Dict[CodeLanguage, List[CodeBlock]]:
        """Group code blocks by programming language."""
        groups = {}
        for block in code_blocks:
            if block.language not in groups:
                groups[block.language] = []
            groups[block.language].append(block)
        return groups
    
    def _generate_file_path(
        self, 
        directory: Path, 
        block: CodeBlock, 
        index: int, #FIXME: "index" is not accessedPylance  
    ) -> Path:
        """Generate appropriate file path for a code block."""

        extension = FILE_EXTENSIONS.get(block.language.value, ".txt")        
        if block.description:
            clean_name = self._clean_filename(block.description)
            filename = f"{clean_name}{extension}"
        else:
            filename = f"{block.id}_{block.language.value}{extension}"
        
        return directory / filename
    
    def _clean_filename(
        self, 
        text: str,
    ) -> str:
        """Clean text to be suitable for filename."""

        import re
        clean = re.sub(r'[^\w\s-]', '', text)
        clean = re.sub(r'[-\s]+', '_', clean)
        return clean.lower()[:50]
    
    def _write_code_file(
        self, 
        file_path: Path, 
        block: CodeBlock,
    ) -> None:
        """Write code block to file with appropriate header."""
        
        header = self._generate_file_header(block)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if header:
                f.write(header)
                f.write('\n\n')
            f.write(block.code)
        
        logger.debug(f"Written code block to: {file_path}")
    
    def _generate_file_header(
        self, 
        block: CodeBlock,
    ) -> str:
        """Generate appropriate header comment for the file."""
        
        if block.language == CodeLanguage.PYTHON:
            prefix = "#"
        elif block.language in [CodeLanguage.JAVASCRIPT, CodeLanguage.TYPESCRIPT, 
                               CodeLanguage.JAVA, CodeLanguage.CPP, CodeLanguage.C,
                               CodeLanguage.CSHARP, CodeLanguage.PHP]:
            prefix = "//"
        elif block.language == CodeLanguage.HTML:
            return f"<!-- Generated by Auto Coder System\n     Block ID: {block.id}\n     Language: {block.language.value} -->"
        elif block.language == CodeLanguage.CSS:
            return f"/* Generated by Auto Coder System\n   Block ID: {block.id}\n   Language: {block.language.value} */"
        elif block.language in [CodeLanguage.BASH, CodeLanguage.SHELL]:
            prefix = "#"
        else:
            prefix = "#"
        
        header_lines = [
            f"{prefix} Generated by Auto Coder System",
            f"{prefix} Block ID: {block.id}",
            f"{prefix} Language: {block.language.value}",
            f"{prefix} Generated at: {datetime.now().isoformat()}"
        ]
        
        if block.description:
            header_lines.append(f"{prefix} Description: {block.description}")
        
        return '\n'.join(header_lines)
    
    def _create_project_metadata(
        self, 
        project_dir: Path, 
        project_name: str, 
        code_blocks: List[CodeBlock],
    ) -> None:
        """Create metadata file for the project."""
        import json

        metadata = {
            "project_name": project_name,
            "created_at": datetime.now().isoformat(),
            "total_blocks": len(code_blocks),
            "languages": list(set(block.language.value for block in code_blocks)),
            "blocks": [
                {
                    "id": block.id,
                    "language": block.language.value,
                    "description": block.description,
                    "file_path": block.file_path
                }
                for block in code_blocks
            ]
        }
        
        metadata_file = project_dir / "project_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    def _create_directory_structure(
        self, 
        base_dir: Path, 
        structure: Dict[str, Any],
    ) -> None:
        """Recursively create directory structure."""

        base_dir.mkdir(parents=True, exist_ok=True)
        
        for name, content in structure.items():
            path = base_dir / name
            
            if isinstance(content, dict):
                self._create_directory_structure(path, content)
            elif isinstance(content, str):
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            else:
                path.mkdir(exist_ok=True) 