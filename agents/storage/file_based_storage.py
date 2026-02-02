# storage/file_based_storage.py
import json
import yaml
import pickle
from pathlib import Path
from typing import Any, Dict, List
from dataclasses import dataclass, asdict

@dataclass
class AgentState:
    """État d'un agent stocké dans des fichiers"""
    agent_id: str
    current_task: Dict[str, Any]
    context: Dict[str, Any]
    memory: List[Dict[str, Any]]
    performance: Dict[str, float]
    
    def save(self, base_path: Path):
        """Sauvegarde l'état dans des fichiers"""
        agent_dir = base_path / self.agent_id
        agent_dir.mkdir(exist_ok=True)
        
        # Sauvegarde en JSON (lisible)
        with open(agent_dir / "state.json", "w") as f:
            json.dump(asdict(self), f, indent=2)
        
        # Sauvegarde en pickle pour la performance
        with open(agent_dir / "state.pkl", "wb") as f:
            pickle.dump(self, f)
        
        # Sauvegarde du contexte séparément
        context_file = agent_dir / "context" / f"context_{datetime.now().timestamp()}.json"
        context_file.parent.mkdir(exist_ok=True)
        with open(context_file, "w") as f:
            json.dump(self.context, f, indent=2)
    
    @classmethod
    def load(cls, agent_id: str, base_path: Path):
        """Charge l'état depuis les fichiers"""
        agent_dir = base_path / agent_id
        
        try:
            # Essaye d'abord le pickle (plus rapide)
            with open(agent_dir / "state.pkl", "rb") as f:
                return pickle.load(f)
        except:
            # Fallback sur JSON
            with open(agent_dir / "state.json", "r") as f:
                data = json.load(f)
                return cls(**data)

class ProjectFileSystem:
    """Gestionnaire du système de fichiers du projet"""
    
    def __init__(self, project_root: Path):
        self.root = project_root
        
        # Structure de base
        self.directories = {
            "agents": self.root / "agents",
            "context": self.root / "context",
            "memory": self.root / "memory",
            "workspace": self.root / "workspace",
            "sprints": self.root / "sprints",
            "reports": self.root / "reports",
            "logs": self.root / "logs",
        }
        
        # Initialisation
        self._init_structure()
    
    def _init_structure(self):
        """Crée la structure de dossiers"""
        for dir_path in self.directories.values():
            dir_path.mkdir(exist_ok=True, parents=True)
            
            # Sous-structure spécifique
            if dir_path.name == "agents":
                for agent_type in ["coder", "tester", "architect", "documenter"]:
                    (dir_path / agent_type).mkdir(exist_ok=True)
            
            if dir_path.name == "memory":
                for sub in ["vector_store", "history", "learnings"]:
                    (dir_path / sub).mkdir(exist_ok=True)
    
    def get_agent_state_path(self, agent_id: str) -> Path:
        """Retourne le chemin de l'état d'un agent"""
        return self.directories["agents"] / agent_id
    
    def save_task_result(self, task_id: str, result: Dict[str, Any]):
        """Sauvegarde le résultat d'une tâche"""
        task_file = self.directories["sprints"] / "current" / f"task_{task_id}.json"
        task_file.parent.mkdir(exist_ok=True)
        
        with open(task_file, "w") as f:
            json.dump({
                "task_id": task_id,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "agent": result.get("agent", "unknown")
            }, f, indent=2)
    
    def load_agent_context(self, agent_id: str, limit: int = 10) -> List[Dict]:
        """Charge le contexte récent d'un agent"""
        context_dir = self.get_agent_state_path(agent_id) / "context"
        
        if not context_dir.exists():
            return []
        
        # Récupère les fichiers de contexte les plus récents
        context_files = sorted(context_dir.glob("*.json"), 
                             key=lambda x: x.stat().st_mtime, 
                             reverse=True)[:limit]
        
        contexts = []
        for file in context_files:
            with open(file, "r") as f:
                contexts.append(json.load(f))
        
        return contexts

# Utilisation
project_fs = ProjectFileSystem(Path("./project_data"))

# Sauvegarde d'état
agent_state = AgentState(
    agent_id="coder_001",
    current_task={"id": "TASK-123", "description": "Implement login"},
    context={"files": ["auth.py"], "dependencies": ["flask"]},
    memory=[{"task": "previous", "result": "success"}],
    performance={"accuracy": 0.95, "speed": 120}
)

agent_state.save(project_fs.get_agent_state_path("coder_001"))