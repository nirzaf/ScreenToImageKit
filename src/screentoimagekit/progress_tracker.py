"""Progress tracking for screenshot workflow."""

import logging
import time
from enum import Enum, auto
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class WorkflowStage(Enum):
    """Stages in the screenshot-to-URL workflow."""
    CAPTURE = auto()
    ANALYSIS = auto()
    RENAME = auto()
    UPLOAD = auto()
    CLIPBOARD = auto()

class ProgressTracker:
    """Tracks and reports progress through the screenshot workflow."""
    
    def __init__(self, status_callback: Callable[[str, bool], None]):
        """Initialize progress tracker.
        
        Args:
            status_callback: Function to call with status updates. Takes message and is_error params.
        """
        self.status_callback = status_callback
        self.current_stage: Optional[WorkflowStage] = None
        self.start_time: float = 0
        
    def _format_duration(self) -> str:
        """Format the duration since stage start."""
        duration = time.time() - self.start_time
        return f" ({duration:.1f}s)" if duration > 1.0 else ""
    
    def start_workflow(self):
        """Start a new screenshot workflow."""
        self.current_stage = None
        self.start_time = time.time()
        self.status_callback("Starting new screenshot...", False)
        logger.info("Starting new screenshot workflow")
    
    def start_stage(self, stage: WorkflowStage):
        """Start tracking a new workflow stage."""
        self.current_stage = stage
        self.start_time = time.time()
        
        messages = {
            WorkflowStage.CAPTURE: "Capturing screenshot...",
            WorkflowStage.ANALYSIS: "Analyzing image content with Gemini AI...",
            WorkflowStage.RENAME: "Renaming file based on AI description...",
            WorkflowStage.UPLOAD: "Uploading image to ImageKit...",
            WorkflowStage.CLIPBOARD: "Copying URL to clipboard..."
        }
        self.status_callback(messages[stage], False)
        logger.info(f"Starting stage: {stage.name}")
    
    def update_progress(self, message: str, is_error: bool = False):
        """Update progress for current stage."""
        full_message = f"{message}{self._format_duration()}"
        self.status_callback(full_message, is_error)
        
        if is_error:
            logger.error(f"Error in workflow: {message}")
        else:
            stage_name = self.current_stage.name if self.current_stage else "workflow"
            logger.info(f"Progress in {stage_name}: {message}")
    
    def stage_complete(self, success_message: str):
        """Mark current stage as complete."""
        if not self.current_stage:
            return
            
        full_message = f"{success_message}{self._format_duration()}"
        self.status_callback(full_message, False)
        logger.info(f"Completed stage {self.current_stage.name}: {success_message}")
        self.current_stage = None
    
    def complete(self):
        """Mark the entire workflow as complete."""
        duration = time.time() - self.start_time
        message = f"Screenshot workflow complete! ({duration:.1f}s)"
        self.status_callback(message, False)
        logger.info("Screenshot workflow complete")
        self.current_stage = None
    
    def reset(self):
        """Reset the progress tracker."""
        self.current_stage = None
        self.start_time = 0
        self.status_callback("Ready", False)
        logger.info("Progress tracker reset")
    
    def upload_progress(self, percent: int):
        """Update upload progress percentage."""
        if self.current_stage == WorkflowStage.UPLOAD:
            self.status_callback(f"Uploading: {percent}%", False)
