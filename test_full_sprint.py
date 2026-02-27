#!/usr/bin/env python3
# test_full_sprint.py - Version SIMPLIFIÉE

import asyncio
import logging
import sys
import os
import json
from datetime import datetime
import yaml
import importlib

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Ajouter le chemin pour les imports
sys.path.insert(0, os.path.dirname(__file__))

# Mapping simplifié : tous les agents utilisent le même pattern
# Le module est toujours "agents.[dossier].agent"
# La classe est "[Nom]Agent" où Nom est le dossier avec première lettre en majuscule

EXCLUDED_AGENTS = ['base_agent', '__pycache__', 'architure']

def get_class_name(agent_dir):
    """Convertit un nom de dossier en nom de classe."""
    # Exemples: architect -> ArchitectAgent
    #           frontend_web3 -> FrontendWeb3Agent
    parts = agent_dir.split('_')
    class_name = ''.join(p.capitalize() for p in parts) + 'Agent'
    return class_name

async def load_all_agents():
    """Charge dynamiquement tous les agents disponibles"""
    
    agents = {}
    failed_imports = []
    agents_dir = os.path.join(os.path.dirname(__file__), 'agents')
    
    print("\n📦 Chargement dynamique de tous les agents...")
    
    for agent_dir in os.listdir(agents_dir):
        agent_path = os.path.join(agents_dir, agent_dir)
        
        if not os.path.isdir(agent_path) or agent_dir in ['base_agent', '__pycache__']:
            continue
        
        try:
            # Le module est toujours agents.[dossier].agent
            module_name = f"agents.{agent_dir}.agent"
            print(f"  🔄 Tentative d'import: {module_name}")
            
            module = importlib.import_module(module_name)
            
            # La classe est [Dossier]Agent (ex: ArchitectAgent)
            class_name = agent_dir.capitalize() + 'Agent'
            if not hasattr(module, class_name):
                # Fallback: chercher n'importe quelle classe avec 'Agent'
                for attr in dir(module):
                    if attr.endswith('Agent') and attr != 'BaseAgent':
                        class_name = attr
                        break
            
            agent_class = getattr(module, class_name)
            
            # Initialiser l'agent
            config_file = os.path.join(agent_path, "config.yaml")
            agent = agent_class(config_file) if os.path.exists(config_file) else agent_class()
            
            await agent.initialize()
            agents[agent_dir] = agent
            logging.info(f"  ✅ Agent {agent_dir} chargé avec succès")
            
        except Exception as e:
            failed_imports.append(f"{agent_dir} ({str(e)})")
    
    return agents

def create_comprehensive_sprint_spec():
    """Crée une spécification de sprint qui teste TOUS les agents"""
    
    spec = {
        "sprint": "SPRINT-ALL-AGENTS",
        "name": "Sprint de test de tous les agents",
        "description": "Sprint complet testant l'ensemble des agents du pipeline",
        "strategy": "largeur_dabord",
        "fragments": [
            {
                "id": "SC_001",
                "domain": "smart_contract",
                "name": "Token ERC20 Complet",
                "description": "Token ERC20 avec mint/burn et permissions",
                "language": "solidity",
                "framework": "foundry",
                "complexity": 2,
                "agents": ["architect", "coder", "smart_contract", "tester"],
                "specification": {
                    "contract_name": "TestToken",
                    "symbol": "TST",
                    "features": ["mint", "burn", "transfer", "approve", "permissions"]
                }
            },
            {
                "id": "SC_002",
                "domain": "smart_contract",
                "name": "Staking Pool Complexe",
                "description": "Pool de staking avec récompenses composées",
                "language": "solidity",
                "framework": "foundry",
                "complexity": 4,
                "agents": ["architect", "coder", "smart_contract", "tester", "formal_verification"],
                "specification": {
                    "contract_name": "TestStaking",
                    "features": ["stake", "unstake", "claim", "compound", "rewards_distribution"],
                    "security": ["reentrancy_guard", "pausable"]
                }
            },
            {
                "id": "BE_001",
                "domain": "backend",
                "name": "API FastAPI Complète",
                "description": "API REST avec endpoints pour tous les contrats",
                "language": "python",
                "framework": "fastapi",
                "complexity": 3,
                "agents": ["architect", "coder", "tester"],
                "specification": {
                    "endpoints": ["/balance", "/transfer", "/stake", "/rewards", "/admin"],
                    "database": "postgresql",
                    "cache": "redis",
                    "auth": "jwt"
                }
            },
            {
                "id": "FE_001",
                "domain": "frontend",
                "name": "Interface Web3 Complète",
                "description": "Application React avec intégration Web3",
                "language": "typescript",
                "framework": "nextjs",
                "complexity": 3,
                "agents": ["frontend_web3", "coder", "tester"],
                "specification": {
                    "pages": ["dashboard", "staking", "admin", "profile"],
                    "wallets": ["metamask", "walletconnect", "coinbase"],
                    "features": ["dark_mode", "responsive", "i18n"]
                }
            },
            {
                "id": "DB_001",
                "domain": "database",
                "name": "Schéma PostgreSQL Optimisé",
                "description": "Base de données complète avec relations et index",
                "language": "sql",
                "framework": "alembic",
                "complexity": 2,
                "agents": ["architect", "storage"],
                "specification": {
                    "tables": ["users", "transactions", "staking_positions", "rewards_history"],
                    "indexes": ["user_address", "timestamp", "status"],
                    "migrations": True
                }
            },
            {
                "id": "DO_001",
                "domain": "devops",
                "name": "Infrastructure Docker/K8s Complète",
                "description": "Déploiement conteneurisé de toute l'application",
                "language": "yaml",
                "version": "docker-compose-v3",
                "complexity": 3,
                "agents": ["architect", "coder"],
                "specification": {
                    "services": ["postgres", "redis", "backend", "frontend", "nginx"],
                    "environments": ["development", "staging", "production"],
                    "monitoring": ["prometheus", "grafana"]
                }
            },
            {
                "id": "DOC_001",
                "domain": "documentation",
                "name": "Documentation Technique Complète",
                "description": "Documentation de tous les composants",
                "language": "markdown",
                "framework": "mkdocs",
                "complexity": 2,
                "agents": ["documenter", "architect"],
                "specification": {
                    "sections": ["introduction", "architecture", "api", "deployment", "user_guide"],
                    "diagrams": ["c4", "sequence", "component"]
                }
            },
            {
                "id": "COM_001",
                "domain": "communication",
                "name": "Système de Communication Inter-Agents",
                "description": "Tests du bus de communication",
                "language": "python",
                "complexity": 2,
                "agents": ["communication", "orchestrator"],
                "specification": {
                    "message_types": ["request", "response", "broadcast"],
                    "patterns": ["pubsub", "request_reply"]
                }
            },
            {
                "id": "SEC_001",
                "domain": "security",
                "name": "Tests de Sécurité Complets",
                "description": "Audit et tests de sécurité de tous les composants",
                "language": "python",
                "complexity": 3,
                "agents": ["tester", "formal_verification", "fuzzing_simulation"],
                "specification": {
                    "tests": ["penetration", "fuzzing", "static_analysis", "formal_verification"],
                    "targets": ["smart_contracts", "api", "frontend"]
                }
            },
            {
                "id": "MON_001",
                "domain": "monitoring",
                "name": "Système de Monitoring Complet",
                "description": "Configuration du monitoring et des alertes",
                "language": "yaml",
                "complexity": 2,
                "agents": ["monitoring"],
                "specification": {
                    "metrics": ["system", "business", "blockchain"],
                    "alerts": ["high_latency", "high_error_rate", "disk_space"],
                    "dashboards": ["backend", "frontend", "blockchain"]
                }
            },
            {
                "id": "LRN_001",
                "domain": "learning",
                "name": "Analyse Prédictive",
                "description": "Modèles d'apprentissage pour optimisation",
                "language": "python",
                "complexity": 3,
                "agents": ["learning", "monitoring"],
                "specification": {
                    "models": ["anomaly_detection", "pattern_recognition", "prediction"],
                    "training_data": ["historical", "simulated"]
                }
            }
        ],
        "dependencies": [
            {"from": "SC_002", "to": "SC_001"},
            {"from": "BE_001", "to": "SC_001"},
            {"from": "BE_001", "to": "DB_001"},
            {"from": "FE_001", "to": "BE_001"},
            {"from": "DO_001", "to": "BE_001"},
            {"from": "DO_001", "to": "FE_001"},
            {"from": "DO_001", "to": "DB_001"},
            {"from": "DOC_001", "to": "*"},
            {"from": "SEC_001", "to": "SC_001"},
            {"from": "SEC_001", "to": "SC_002"},
            {"from": "SEC_001", "to": "BE_001"},
            {"from": "MON_001", "to": "DO_001"},
            {"from": "LRN_001", "to": "MON_001"}
        ],
        "quality_gates": {
            "test_coverage": 85,
            "security_audit_required": True,
            "performance_sla_ms": 200
        }
    }
    
    # Sauvegarder la spécification
    os.makedirs("specs/projects", exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    spec_file = f"specs/projects/sprint_all_agents_{timestamp}.json"
    with open(spec_file, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    print(f"\n📝 Spécification créée: {spec_file}")
    print(f"📊 Fragments: {len(spec['fragments'])}")
    
    return spec_file

async def main():
    print("\n" + "="*70)
    print("🚀 TEST COMPLET DE TOUS LES AGENTS DU PIPELINE")
    print("="*70 + "\n")
    
    # Charger tous les agents disponibles
    agents = await load_all_agents()
    
    if 'orchestrator' not in agents:
        print("\n❌ Orchestrator non disponible - arrêt du test")
        return
    
    orchestrator = agents['orchestrator']
    
    # Créer une spécification qui teste tous les agents
    print("\n📋 Création d'une spécification de sprint complète...")
    spec_file = create_comprehensive_sprint_spec()
    
    # Vérifier les agents disponibles
    if agents:
        print(f"\n✅ Agents disponibles ({len(agents)}): {', '.join(agents.keys())}")
    else:
        print("\n⚠️ Aucun agent chargé - vérifiez les erreurs ci-dessus")
        return
    
    # Exécuter le sprint
    print("\n🚀 Lancement du sprint complet...")
    report = await orchestrator.execute_sprint(spec_file)
    
    print(f"\n" + "="*70)
    print(f"✅ SPRINT TERMINÉ")
    print(f"📊 Fragments: {report['metrics']['total_fragments']}")
    print(f"📈 Succès: {report['metrics']['success_rate']:.1f}%")
    
    # Afficher les fragments en échec
    if 'failed_fragments' in report['metrics'] and report['metrics']['failed_fragments']:
        failed = report['metrics']['failed_fragments']
        print(f"\n❌ Fragments en échec ({len(failed)}):")
        for f in failed:
            print(f"   • {f}")
    
    if 'recommendations' in report:
        print(f"\n💡 Recommandations:")
        for rec in report['recommendations']:
            print(f"   • {rec}")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    asyncio.run(main())