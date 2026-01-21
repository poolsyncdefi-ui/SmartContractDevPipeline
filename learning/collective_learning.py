# learning/collective_learning.py
import hashlib
from typing import Dict, List
from pathlib import Path

class CollectiveLearningSystem:
    """Système d'apprentissage partagé basé sur fichiers"""
    
    def __init__(self, knowledge_base_path: Path):
        self.knowledge_base = knowledge_base_path
        self.knowledge_base.mkdir(exist_ok=True)
        
        # Sous-répertoires
        self.patterns_dir = self.knowledge_base / "patterns"
        self.solutions_dir = self.knowledge_base / "solutions"
        self.mistakes_dir = self.knowledge_base / "mistakes"
        self.best_practices_dir = self.knowledge_base / "best_practices"
        
        for dir in [self.patterns_dir, self.solutions_dir, 
                   self.mistakes_dir, self.best_practices_dir]:
            dir.mkdir(exist_ok=True)
    
    def store_solution(self, problem_hash: str, solution: Dict, agent_id: str):
        """Stocke une solution à un problème"""
        solution_file = self.solutions_dir / f"{problem_hash}.json"
        
        data = {
            "problem_hash": problem_hash,
            "solution": solution,
            "agent": agent_id,
            "timestamp": datetime.now().isoformat(),
            "effectiveness": 1.0,  # Sera mis à jour avec le feedback
            "usage_count": 1
        }
        
        if solution_file.exists():
            # Mise à jour du compteur d'utilisation
            with open(solution_file, "r") as f:
                existing = json.load(f)
                existing["usage_count"] += 1
            
            data = existing
        
        with open(solution_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def find_similar_solutions(self, problem_description: str, 
                              threshold: float = 0.8) -> List[Dict]:
        """Trouve des solutions similaires"""
        problem_hash = self._hash_description(problem_description)
        
        solutions = []
        for solution_file in self.solutions_dir.glob("*.json"):
            with open(solution_file, "r") as f:
                solution_data = json.load(f)
                
                # Calcul de similarité basique
                similarity = self._calculate_similarity(
                    problem_hash, 
                    solution_data["problem_hash"]
                )
                
                if similarity >= threshold:
                    solutions.append(solution_data)
        
        return sorted(solutions, key=lambda x: x["effectiveness"], reverse=True)
    
    def learn_from_mistake(self, agent_id: str, task: Dict, 
                          error: str, correction: Dict):
        """Apprend d'une erreur et la partage"""
        mistake_id = f"{agent_id}_{datetime.now().timestamp()}"
        mistake_file = self.mistakes_dir / f"{mistake_id}.json"
        
        with open(mistake_file, "w") as f:
            json.dump({
                "agent": agent_id,
                "task": task,
                "error": error,
                "correction": correction,
                "timestamp": datetime.now().isoformat(),
                "learned_by": [agent_id]  # Liste des agents ayant appris
            }, f, indent=2)
        
        # Notifie les autres agents
        self._broadcast_learning(agent_id, "mistake_learned", mistake_id)
    
    def _broadcast_learning(self, from_agent: str, learning_type: str, 
                          content_id: str):
        """Diffuse un apprentissage à tous les agents"""
        learning_event = {
            "type": learning_type,
            "from": from_agent,
            "content_id": content_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Écrit dans un fichier partagé que tous les agents lisent
        event_file = self.knowledge_base / "learning_events.jsonl"
        
        with open(event_file, "a") as f:
            f.write(json.dumps(learning_event) + "\n")
    
    @staticmethod
    def _hash_description(description: str) -> str:
        """Hash une description pour comparaison"""
        return hashlib.md5(description.encode()).hexdigest()[:10]
    
    @staticmethod
    def _calculate_similarity(hash1: str, hash2: str) -> float:
        """Calcule la similarité entre deux hashes"""
        # Simple similarité de Levenshtein normalisée
        from Levenshtein import distance
        max_len = max(len(hash1), len(hash2))
        if max_len == 0:
            return 1.0
        return 1 - distance(hash1, hash2) / max_len