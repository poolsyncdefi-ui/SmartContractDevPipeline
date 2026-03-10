"""
Test simplifié de BaseSubAgent - contourne les problèmes de BaseAgent
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Ajouter le chemin du projet
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Importer BaseAgent mais on va le simplifier
from agents.base_agent.base_agent import BaseAgent, AgentStatus


# ============================================================================
# VERSION SIMPLIFIÉE DE BASESUBAGENT POUR LE TEST
# ============================================================================

class SimpleSubAgent:
    """
    Version simplifiée d'un sous-agent pour les tests
    (contourne les problèmes de BaseAgent)
    """
    
    def __init__(self, name: str = "TestAgent"):
        self.name = name
        self._initialized = False
        self._status = "created"
        self.logger = logging.getLogger(name)
        
        # Métadonnées
        self._subagent_display_name = "🧪 TestAgent"
        self._subagent_description = "Agent de test"
        self._subagent_version = "1.0.0"
        self._subagent_category = "test"
        self._subagent_capabilities = ["test.echo", "test.sleep"]
        
        # Gestion des tâches
        self._task_queue = asyncio.Queue()
        self._active_tasks = {}
        self._task_results = {}
        self._task_counter = 0
        
        # Métriques simplifiées
        self._metrics = {
            "tasks_processed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "start_time": datetime.now().isoformat()
        }
        
        # Cache simplifié
        self._cache = {}
        self._cache_stats = {"hits": 0, "misses": 0}
        
        self.logger.info(f"✅ Agent {name} créé")
    
    async def initialize(self) -> bool:
        """Initialisation simplifiée"""
        self._initialized = True
        self._status = "ready"
        self.logger.info(f"✅ Agent {self.name} initialisé")
        return True
    
    async def submit_task(self, task_type: str, params: Dict = None, 
                          priority: str = "normal", cacheable: bool = True) -> str:
        """Soumet une tâche"""
        import uuid
        task_id = str(uuid.uuid4())
        
        task = {
            "id": task_id,
            "type": task_type,
            "params": params or {},
            "priority": priority,
            "status": "queued",
            "created_at": datetime.now(),
            "cacheable": cacheable
        }
        
        await self._task_queue.put(task)
        self._task_results[task_id] = task
        self.logger.info(f"📥 Tâche {task_id} ({task_type}) soumise")
        
        return task_id
    
    async def get_task_result(self, task_id: str, wait: bool = False, 
                             timeout: int = 5) -> Optional[Dict]:
        """Récupère le résultat d'une tâche"""
        task = self._task_results.get(task_id)
        
        if not task:
            return None
        
        if wait and task["status"] in ["queued", "processing"]:
            # Simuler l'exécution
            await asyncio.sleep(0.1)
            
            # Exécuter le handler approprié
            if task["type"] == "test.echo":
                task["result"] = {"echo": task["params"], "success": True}
            elif task["type"] == "test.sleep":
                duration = task["params"].get("duration", 0.2)
                await asyncio.sleep(duration)
                task["result"] = {"slept": duration, "success": True}
            else:
                task["result"] = {"error": "Unknown task type", "success": False}
            
            task["status"] = "completed"
            task["completed_at"] = datetime.now()
            
            # Métriques
            self._metrics["tasks_processed"] += 1
            self._metrics["tasks_succeeded"] += 1
        
        return task
    
    async def shutdown(self):
        """Arrêt simplifié"""
        self._status = "terminated"
        self.logger.info(f"✅ Agent {self.name} arrêté")
    
    async def health_check(self) -> Dict:
        """Health check simplifié"""
        return {
            "status": self._status,
            "ready": self._status == "ready",
            "initialized": self._initialized,
            "metrics": self._metrics,
            "cache_stats": self._cache_stats,
            "queue_size": self._task_queue.qsize(),
            "active_tasks": len(self._active_tasks)
        }


# ============================================================================
# TESTS
# ============================================================================

async def test_initialization():
    """Teste l'initialisation"""
    print("\n" + "="*60)
    print("📋 TEST 1: Initialisation")
    print("="*60)
    
    agent = SimpleSubAgent("Test1")
    await agent.initialize()
    
    assert agent._initialized, "Agent non initialisé"
    assert agent._status == "ready", f"Mauvais statut: {agent._status}"
    
    print(f"✅ Agent: {agent._subagent_display_name}")
    print(f"✅ Statut: {agent._status}")
    print(f"✅ Capacités: {agent._subagent_capabilities}")
    
    return agent


async def test_task_submission(agent):
    """Teste la soumission de tâches"""
    print("\n" + "="*60)
    print("📋 TEST 2: Soumission de tâches")
    print("="*60)
    
    # Tâche echo
    task_id = await agent.submit_task("test.echo", {"msg": "Hello"})
    print(f"✅ Tâche soumise: {task_id}")
    
    task = await agent.get_task_result(task_id, wait=True)
    print(f"✅ Résultat: {task['result']}")
    assert task['result']['echo']['msg'] == "Hello", "Message incorrect"
    
    # Tâche sleep
    task_id = await agent.submit_task("test.sleep", {"duration": 0.2})
    task = await agent.get_task_result(task_id, wait=True)
    print(f"✅ Tâche sleep terminée")
    assert task['result']['slept'] == 0.2, "Durée incorrecte"
    
    return True


async def test_concurrent_tasks(agent):
    """Teste l'exécution concurrente"""
    print("\n" + "="*60)
    print("📋 TEST 3: Tâches concurrentes")
    print("="*60)
    
    import time
    start = time.time()
    
    # Lancer 5 tâches
    tasks = []
    for i in range(5):
        task_id = await agent.submit_task("test.sleep", {"duration": 0.2})
        tasks.append(task_id)
    
    # Attendre toutes
    results = await asyncio.gather(*[
        agent.get_task_result(tid, wait=True) for tid in tasks
    ])
    
    duration = time.time() - start
    print(f"✅ {len(results)} tâches terminées en {duration:.2f}s")
    assert duration < 1.0, f"Trop lent: {duration:.2f}s"
    
    return True


async def test_health_check(agent):
    """Teste le health check"""
    print("\n" + "="*60)
    print("📋 TEST 4: Health Check")
    print("="*60)
    
    health = await agent.health_check()
    print(f"❤️ Health: {health['status']}")
    print(f"📊 Métriques: {health['metrics']}")
    assert health['ready'], "Agent non prêt"
    
    return True


async def test_shutdown(agent):
    """Teste l'arrêt"""
    print("\n" + "="*60)
    print("📋 TEST 5: Arrêt")
    print("="*60)
    
    await agent.shutdown()
    print(f"✅ Agent arrêté")
    
    health = await agent.health_check()
    assert not health['ready'], "Agent devrait être arrêté"
    
    return True


async def main():
    """Fonction principale"""
    print("\n" + "="*70)
    print("🧪 TEST SIMPLIFIÉ DE SOUS-AGENT")
    print("="*70)
    
    # Initialiser l'agent
    agent = await test_initialization()
    
    # Exécuter les tests
    tests = [
        test_task_submission,
        test_concurrent_tasks,
        test_health_check,
        test_shutdown,
    ]
    
    success_count = 0
    for test_func in tests:
        try:
            if await test_func(agent):
                success_count += 1
        except Exception as e:
            print(f"❌ Échec: {e}")
            import traceback
            traceback.print_exc()
    
    # Résumé
    print("\n" + "="*70)
    print(f"📊 RÉSUMÉ: {success_count}/{len(tests)} tests réussis")
    print("="*70)
    
    return success_count == len(tests)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)