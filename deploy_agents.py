#!/usr/bin/env python3
"""
Script principal de déploiement des agents - Version corrigée
"""
import os
import sys
import subprocess
import yaml
from pathlib import Path

def create_directory_structure():
    """Crée la structure complète des répertoires"""
    structure = {
        # Agents principaux
        "agents/main/architect": ["__init__.py", "config.yaml", "agent.py", "orchestrator.py"],
        "agents/main/coder": ["__init__.py", "config.yaml", "agent.py", "orchestrator.py"],
        "agents/main/smart_contract": ["__init__.py", "config.yaml", "agent.py", "orchestrator.py"],
        "agents/main/communication": ["__init__.py", "config.yaml", "agent.py", "message_bus.py"],
        "agents/main/documenter": ["__init__.py", "config.yaml", "agent.py", "orchestrator.py"],
        "agents/main/formal_verification": ["__init__.py", "config.yaml", "agent.py", "orchestrator.py"],
        "agents/main/frontend_web3": ["__init__.py", "config.yaml", "agent.py", "orchestrator.py"],
        "agents/main/quality_metrics": ["__init__.py", "config.yaml", "agent.py", "orchestrator.py"],
        "agents/main/tester": ["__init__.py", "config.yaml", "agent.py", "orchestrator.py"],
        
        # Sous-agents
        "agents/sub/architecture/cloud": ["__init__.py", "config.yaml", "agent.py", "tools.py"],
        "agents/sub/architecture/blockchain": ["__init__.py", "config.yaml", "agent.py", "tools.py"],
        "agents/sub/architecture/microservices": ["__init__.py", "config.yaml", "agent.py", "tools.py"],
        
        # Micro-agents
        "agents/micro/database": ["__init__.py", "config.yaml", "agent.py"],
        "agents/micro/cache": ["__init__.py", "config.yaml", "agent.py"],
        "agents/micro/api_gateway": ["__init__.py", "config.yaml", "agent.py"],
        
        # Communication
        "agents/communication/zeromq": ["__init__.py", "config.yaml", "message_bus.py", "publisher.py", "subscriber.py"],
        "agents/communication/redis": ["__init__.py", "config.yaml", "pubsub.py", "event_handler.py"],
        
        # Orchestration
        "agents/orchestration/master": ["__init__.py", "config.yaml", "orchestrator.py", "scheduler.py", "monitor.py"],
    }
    
    created_count = 0
    for directory, files in structure.items():
        # Créer le répertoire
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Créer les fichiers
        for file in files:
            file_path = Path(directory) / file
            if not file_path.exists():
                if file.endswith('.py'):
                    # Fichier Python minimal
                    if file == "__init__.py":
                        file_path.write_text("# Package initializer\n")
                    elif file == "config.yaml":
                        file_path.write_text(f"# Configuration for {directory}\nname: {Path(directory).name}\n")
                    else:
                        file_path.write_text(f"# {file} for {directory}\n# TODO: Implement this module\n")
                created_count += 1
    
    return created_count

def install_dependencies():
    """Installe les dépendances Python requises"""
    dependencies = [
        "pyzmq>=25.0.0",
        "redis>=5.0.0",
        "pyyaml>=6.0",
        "pydantic>=2.0.0",
        "asyncio-mqtt>=0.13.0",
        "websockets>=12.0",
    ]
    
    print("📦 Installation des dépendances Python...")
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"  ✅ {dep}")
        except subprocess.CalledProcessError:
            print(f"  ❌ Échec installation: {dep}")
    
    return True

def create_main_config():
    """Crée le fichier de configuration principal"""
    config = {
        "project": "PoolSync-Agents",
        "version": "1.0.0",
        "communication": {
            "zeromq": {
                "host": "127.0.0.1",
                "pub_port": 5555,
                "sub_port": 5556,
                "router_port": 5557
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0
            }
        },
        "agents": {
            "auto_start": ["architect", "coder", "communication"],
            "health_check_interval": 30,
            "log_level": "INFO"
        },
        "security": {
            "api_keys": {},
            "encryption_enabled": False,
            "auth_required": True
        }
    }
    
    config_path = Path("config") / "main.yaml"
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"📄 Configuration créée: {config_path}")
    return config_path

def setup_logging():
    """Configure le système de logging"""
    logging_config = """version: 1
formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handlers:
  console:
    class: logging.StreamHandler
    formatter: standard
    level: INFO
  file:
    class: logging.handlers.RotatingFileHandler
    formatter: standard
    filename: logs/agents.log
    maxBytes: 10485760
    backupCount: 5
    level: DEBUG
loggers:
  agents:
    level: DEBUG
    handlers: [console, file]
    propagate: no
root:
  level: INFO
  handlers: [console]
"""
    
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    config_path = Path("config") / "logging.yaml"
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w') as f:
        f.write(logging_config)
    
    print(f"📝 Configuration logging créée: {config_path}")
    return config_path

def create_example_agent():
    """Crée un exemple d'agent de démonstration"""
    example_code = '''"""
Agent de démonstration pour PoolSync
"""
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from agents.communication.zeromq.message_bus import ZeroMQMessageBus, Message

logger = logging.getLogger(__name__)

class DemoAgent:
    """Agent de démonstration avec communication ZeroMQ"""
    
    def __init__(self, agent_id: str, message_bus: ZeroMQMessageBus):
        self.agent_id = agent_id
        self.message_bus = message_bus
        self.running = False
        
    async def start(self):
        """Démarre l'agent"""
        self.running = True
        
        # S'abonner aux messages
        self.message_bus.subscribe(
            agent_id=self.agent_id,
            message_types=["demo.command", "system.status"],
            handler=self.handle_message
        )
        
        logger.info(f"Agent {self.agent_id} démarré")
        
        # Boucle principale
        while self.running:
            try:
                # Envoyer un heartbeat
                await self.send_heartbeat()
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Erreur dans l'agent {self.agent_id}: {e}")
                await asyncio.sleep(5)
    
    async def send_heartbeat(self):
        """Envoie un heartbeat"""
        message = Message(
            id=f"heartbeat-{datetime.now().timestamp()}",
            sender=self.agent_id,
            receivers=["orchestrator"],
            message_type="agent.heartbeat",
            content={
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat(),
                "status": "running"
            },
            requires_ack=False
        )
        
        self.message_bus.publish(message)
        logger.debug(f"Heartbeat envoyé par {self.agent_id}")
    
    def handle_message(self, message: Message):
        """Traite un message reçu"""
        logger.info(f"{self.agent_id} reçu message: {message.message_type}")
        
        if message.message_type == "demo.command":
            self.process_command(message.content)
        elif message.message_type == "system.status":
            self.report_status()
    
    def process_command(self, command: Dict[str, Any]):
        """Traite une commande"""
        action = command.get("action")
        
        if action == "echo":
            response = Message(
                sender=self.agent_id,
                receivers=[command.get("from", "unknown")],
                message_type="demo.response",
                content={"echo": command.get("data", ""), "processed_by": self.agent_id}
            )
            self.message_bus.publish(response)
            logger.info(f"{self.agent_id} a traité la commande: {action}")
    
    def report_status(self):
        """Reporte le statut de l'agent"""
        status = {
            "agent_id": self.agent_id,
            "running": self.running,
            "timestamp": datetime.now().isoformat()
        }
        
        message = Message(
            sender=self.agent_id,
            receivers=["monitor"],
            message_type="agent.status",
            content=status
        )
        
        self.message_bus.publish(message)
    
    async def stop(self):
        """Arrête l'agent"""
        self.running = False
        logger.info(f"Agent {self.agent_id} arrêté")

async def main():
    """Fonction principale de démonstration"""
    # Initialiser le bus de messages
    message_bus = ZeroMQMessageBus(host="127.0.0.1", pub_port=5555)
    message_bus.start()
    
    # Créer un agent de démonstration
    demo_agent = DemoAgent(agent_id="demo_agent_1", message_bus=message_bus)
    
    try:
        # Démarrer l'agent
        await demo_agent.start()
    except KeyboardInterrupt:
        print("\\nArrêt demandé...")
    finally:
        # Nettoyage
        await demo_agent.stop()
        message_bus.stop()

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    demo_path = Path("examples") / "demo_agent.py"
    demo_path.parent.mkdir(exist_ok=True)
    
    with open(demo_path, 'w') as f:
        f.write(example_code)
    
    print(f"🎯 Exemple d'agent créé: {demo_path}")
    return demo_path

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🚀 DÉPLOIEMENT DES AGENTS POOLSYNC - VERSION CORRIGÉE")
    print("=" * 60)
    
    try:
        # 1. Créer la structure
        print("\n1. 📁 Création de la structure des répertoires...")
        created = create_directory_structure()
        print(f"   ✅ {created} fichiers/dossiers créés")
        
        # 2. Installer les dépendances
        print("\n2. 📦 Installation des dépendances...")
        install_dependencies()
        
        # 3. Configuration
        print("\n3. ⚙️  Configuration du système...")
        create_main_config()
        setup_logging()
        
        # 4. Exemples
        print("\n4. 🔧 Création des exemples...")
        create_example_agent()
        
        # 5. Fichier README
        readme = """# 🏗️ PoolSync Agents System

## Architecture Multi-Agents Corrigée

Ce système implémente une architecture multi-agents pour le développement DeFi.

### Structure Principale
