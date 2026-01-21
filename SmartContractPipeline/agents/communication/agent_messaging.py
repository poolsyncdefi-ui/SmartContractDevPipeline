# agents/communication/agent_messaging.py
class AgentMessage:
    """Format standardisé des messages entre agents"""
    
    def __init__(self, sender: str, receiver: str, message_type: str):
        self.sender = sender
        self.receiver = receiver
        self.message_type = message_type
        self.timestamp = datetime.now()
        self.message_id = str(uuid.uuid4())
        
    @dataclass
    class Content:
        task_id: str
        context: dict
        payload: Any  # Code, test results, docs, etc.
        dependencies: List[str]
        priority: int = 1
        requires_response: bool = True
        timeout_seconds: int = 300

# Types de messages supportés
MESSAGE_TYPES = {
    # Code-related
    "code_review_request": {"from": "coder", "to": "reviewer"},
    "code_review_completed": {"from": "reviewer", "to": "coder"},
    "test_execution_request": {"from": "coder", "to": "tester"},
    "test_results_ready": {"from": "tester", "to": "coder"},
    
    # Documentation
    "doc_generation_request": {"from": "coder", "to": "documenter"},
    "doc_review_needed": {"from": "documenter", "to": "reviewer"},
    
    # Architecture & Planning
    "architecture_approval_needed": {"from": "architect", "to": "orchestrator"},
    "task_completion_notification": {"from": "any", "to": "orchestrator"},
    
    # Quality & Security
    "security_scan_request": {"from": "orchestrator", "to": "security"},
    "quality_gate_failed": {"from": "tester", "to": "orchestrator"},
    
    # Human intervention
    "human_approval_needed": {"from": "any", "to": "human"},
    "blocker_identified": {"from": "any", "to": "orchestrator"},
}

# Système de priorité
PRIORITY_LEVELS = {
    "CRITICAL": 1,    # Bloque le pipeline
    "HIGH": 2,        # Nécessite attention immédiate
    "MEDIUM": 3,      # Doit être traité aujourd'hui
    "LOW": 4,         # Peut attendre
    "INFO": 5,        # Notification seulement
}