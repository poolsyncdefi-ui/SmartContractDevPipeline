#!/usr/bin/env python3
# test_full_sprint.py - Version ULTRA-VERBOSE avec scan complet des agents et sous-agents

import asyncio
import logging
import sys
import os
import json
from datetime import datetime
import yaml
import importlib
import traceback
import inspect

# Configuration du logging ULTRA-VERBOSE
logging.basicConfig(
    level=logging.DEBUG,  # Passage en DEBUG pour voir absolument tout
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Ajouter le chemin pour les imports
sys.path.insert(0, os.path.dirname(__file__))

# === LISTE DES AGENTS À EXCLURE ===
EXCLUDED_AGENTS = [
    'base_agent',           # Agent de base (abstrait)
    '__pycache__',          # Dossier cache
    'architure',            # Dossier avec faute d'orthographe
    'database',             # Agent database non développé
]

# ============================================================================
# FONCTIONS DE SCAN ULTRA-VERBOSE
# ============================================================================

def scan_all_agents_and_subagents_verbose(agents_dir: str = "agents") -> dict:
    """
    Scanne TOUS les agents et sous-agents avec logging ultra-détaillé
    Retourne un dictionnaire complet de la structure
    """
    print("\n" + "="*80)
    print("🔍 SCAN ULTRA-VERBOSE DE TOUS LES AGENTS ET SOUS-AGENTS")
    print("="*80)
    
    agents_path = os.path.join(os.path.dirname(__file__), agents_dir)
    print(f"📂 Dossier agents: {agents_path}")
    
    if not os.path.exists(agents_path):
        print(f"❌ Dossier introuvable: {agents_path}")
        return {}
    
    structure = {
        "agents_principaux": {},
        "sous_agents": {},
        "stats": {
            "total_agents": 0,
            "total_sous_agents": 0,
            "fichiers_py": 0,
            "fichiers_yaml": 0,
            "fichiers_json": 0,
            "fichiers_md": 0,
            "total_fichiers": 0
        }
    }
    
    print("\n📋 LISTE COMPLÈTE DES AGENTS DÉTECTÉS")
    print("-"*80)
    
    for agent_dir in sorted(os.listdir(agents_path)):
        agent_full_path = os.path.join(agents_path, agent_dir)
        
        if not os.path.isdir(agent_full_path):
            continue
        
        if agent_dir in EXCLUDED_AGENTS:
            print(f"⏭️  Agent exclu: {agent_dir}")
            continue
        
        print(f"\n📦 AGENT PRINCIPAL: {agent_dir}")
        print(f"   📁 Chemin: {agent_full_path}")
        
        # Scanner les fichiers de l'agent principal
        agent_files = scan_directory_verbose(agent_full_path, f"   {agent_dir}")
        
        structure["agents_principaux"][agent_dir] = {
            "path": agent_full_path,
            "files": agent_files
        }
        
        # Mettre à jour les stats
        structure["stats"]["total_agents"] += 1
        for ext in agent_files["by_extension"]:
            if ext == '.py':
                structure["stats"]["fichiers_py"] += agent_files["by_extension"][ext]
            elif ext in ['.yaml', '.yml']:
                structure["stats"]["fichiers_yaml"] += agent_files["by_extension"][ext]
            elif ext == '.json':
                structure["stats"]["fichiers_json"] += agent_files["by_extension"][ext]
            elif ext == '.md':
                structure["stats"]["fichiers_md"] += agent_files["by_extension"][ext]
        
        # Scanner les sous-agents
        sous_agents_path = os.path.join(agent_full_path, "sous_agents")
        if os.path.exists(sous_agents_path) and os.path.isdir(sous_agents_path):
            print(f"\n   🔽 SOUS-AGENTS de {agent_dir}:")
            
            for sous_agent_dir in sorted(os.listdir(sous_agents_path)):
                sous_agent_full_path = os.path.join(sous_agents_path, sous_agent_dir)
                
                if not os.path.isdir(sous_agent_full_path) or sous_agent_dir.startswith('__'):
                    continue
                
                print(f"\n      📦 SOUS-AGENT: {sous_agent_dir}")
                print(f"         📁 Chemin: {sous_agent_full_path}")
                
                # Scanner les fichiers du sous-agent
                sous_agent_files = scan_directory_verbose(sous_agent_full_path, f"         {agent_dir}.{sous_agent_dir}")
                
                if agent_dir not in structure["sous_agents"]:
                    structure["sous_agents"][agent_dir] = {}
                
                structure["sous_agents"][agent_dir][sous_agent_dir] = {
                    "path": sous_agent_full_path,
                    "files": sous_agent_files
                }
                
                structure["stats"]["total_sous_agents"] += 1
                
                # Mettre à jour les stats
                for ext in sous_agent_files["by_extension"]:
                    if ext == '.py':
                        structure["stats"]["fichiers_py"] += sous_agent_files["by_extension"][ext]
                    elif ext in ['.yaml', '.yml']:
                        structure["stats"]["fichiers_yaml"] += sous_agent_files["by_extension"][ext]
                    elif ext == '.json':
                        structure["stats"]["fichiers_json"] += sous_agent_files["by_extension"][ext]
                    elif ext == '.md':
                        structure["stats"]["fichiers_md"] += sous_agent_files["by_extension"][ext]
    
    structure["stats"]["total_fichiers"] = (
        structure["stats"]["fichiers_py"] +
        structure["stats"]["fichiers_yaml"] +
        structure["stats"]["fichiers_json"] +
        structure["stats"]["fichiers_md"]
    )
    
    # Afficher les statistiques
    print("\n" + "="*80)
    print("📊 STATISTIQUES DU SCAN")
    print("="*80)
    print(f"📦 Agents principaux: {structure['stats']['total_agents']}")
    print(f"📦 Sous-agents: {structure['stats']['total_sous_agents']}")
    print(f"🐍 Fichiers Python: {structure['stats']['fichiers_py']}")
    print(f"⚙️ Fichiers YAML: {structure['stats']['fichiers_yaml']}")
    print(f"📋 Fichiers JSON: {structure['stats']['fichiers_json']}")
    print(f"📝 Fichiers Markdown: {structure['stats']['fichiers_md']}")
    print(f"📊 TOTAL FICHIERS: {structure['stats']['total_fichiers']}")
    print("="*80)
    
    return structure


def scan_directory_verbose(directory: str, prefix: str = "") -> dict:
    """Scanne un répertoire et retourne les fichiers avec stats"""
    files = {
        "list": [],
        "by_extension": {}
    }
    
    extensions = ['.py', '.yaml', '.yml', '.json', '.md', '.txt', '.sol', '.js', '.ts']
    
    for item in sorted(os.listdir(directory)):
        item_path = os.path.join(directory, item)
        
        if item.startswith('__') or item.startswith('.'):
            continue
        
        if os.path.isfile(item_path):
            ext = os.path.splitext(item)[1].lower()
            if ext in extensions:
                files["list"].append(item)
                files["by_extension"][ext] = files["by_extension"].get(ext, 0) + 1
                
                # Emoji par type
                if ext == '.py':
                    emoji = "🐍"
                elif ext in ['.yaml', '.yml']:
                    emoji = "⚙️"
                elif ext == '.json':
                    emoji = "📋"
                elif ext == '.md':
                    emoji = "📝"
                else:
                    emoji = "📄"
                
                print(f"   {prefix} {emoji} {item}")
    
    return files


def get_class_name(agent_dir):
    """Convertit un nom de dossier en nom de classe."""
    parts = agent_dir.split('_')
    class_name = ''.join(p.capitalize() for p in parts) + 'Agent'
    return class_name


def analyze_agent_module_verbose(module, agent_dir: str, is_subagent: bool = False):
    """Analyse en détail un module d'agent"""
    print(f"\n      🔍 ANALYSE DÉTAILLÉE DU MODULE:")
    
    # Lister toutes les classes
    classes = []
    for name, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ == module.__name__:  # Classe définie dans ce module
            classes.append(name)
    
    print(f"         📋 Classes trouvées: {', '.join(classes) if classes else 'aucune'}")
    
    # Chercher la classe Agent
    agent_class = None
    found_by = ""
    
    # Méthode 1: get_class_name
    candidate = get_class_name(agent_dir)
    if hasattr(module, candidate):
        agent_class = candidate
        found_by = f"get_class_name ({candidate})"
    
    # Méthode 2: *Agent
    if not agent_class:
        for cls in classes:
            if cls.endswith('Agent') and cls != 'BaseAgent':
                agent_class = cls
                found_by = f"classe *Agent ({cls})"
                break
    
    # Méthode 3: contient le nom du dossier
    if not agent_class:
        base_name = agent_dir.replace('_', '').lower()
        for cls in classes:
            if base_name in cls.lower():
                agent_class = cls
                found_by = f"contient '{base_name}' ({cls})"
                break
    
    if agent_class:
        print(f"         ✅ Classe Agent trouvée: {agent_class} (par {found_by})")
        return agent_class
    else:
        print(f"         ❌ Aucune classe Agent trouvée!")
        return None


def safe_import_module_verbose(module_name: str, agent_dir: str):
    """Tente d'importer un module avec logging détaillé"""
    print(f"\n      🔄 Tentatives d'import pour {agent_dir}:")
    
    base_module = f"agents.{agent_dir}"
    variants = [
        f"{base_module}.agent",                    # agents.coder.agent
        base_module,                                # agents.coder
        f"{base_module}.{agent_dir}",               # agents.coder.coder
        f"{base_module}.{agent_dir}_agent",         # agents.coder.coder_agent
        f"{base_module}.agent_{agent_dir}",         # agents.coder.agent_coder
    ]
    
    # Enlever les doublons
    variants = list(dict.fromkeys(variants))
    
    for i, variant in enumerate(variants, 1):
        try:
            print(f"         {i}. Tentative: {variant}")
            module = importlib.import_module(variant)
            print(f"            ✅ RÉUSSI!")
            return module, variant
        except ImportError as e:
            print(f"            ❌ Échec: {str(e)}")
            continue
    
    raise ImportError(f"Aucune variante trouvée pour {agent_dir}")


# ============================================================================
# FONCTION PRINCIPALE DE CHARGEMENT ULTRA-VERBOSE
# ============================================================================

async def load_all_agents_verbose():
    """Charge dynamiquement tous les agents avec logging ULTRA-VERBOSE"""
    
    print("\n" + "="*80)
    print("🚀 CHARGEMENT DYNAMIQUE ULTRA-VERBOSE DE TOUS LES AGENTS")
    print("="*80)
    
    # Étape 1: Scanner tous les agents
    structure = scan_all_agents_and_subagents_verbose()
    
    agents = {}
    failed_imports = []
    agents_dir = os.path.join(os.path.dirname(__file__), 'agents')
    
    stats = {
        'total_agents': structure['stats']['total_agents'],
        'total_sous_agents': structure['stats']['total_sous_agents'],
        'imported': 0,
        'initialized': 0,
        'partial': 0,
        'failed_import': 0,
        'failed_init': 0
    }
    
    # Étape 2: Charger les agents principaux
    print("\n" + "="*80)
    print("📦 CHARGEMENT DES AGENTS PRINCIPAUX")
    print("="*80)
    
    for agent_dir in structure['agents_principaux']:
        print(f"\n{'='*60}")
        print(f"📦 AGENT: {agent_dir}")
        print(f"{'='*60}")
        
        agent_path = os.path.join(agents_dir, agent_dir)
        warnings = []
        
        try:
            # Étape 2.1: Import du module
            print(f"\n   ÉTAPE 1: Import du module")
            print(f"   {'-'*40}")
            
            module_name = f"agents.{agent_dir}.agent"
            try:
                module, used_variant = safe_import_module_verbose(module_name, agent_dir)
                stats['imported'] += 1
            except ImportError as e:
                stats['failed_import'] += 1
                failed_imports.append(f"{agent_dir} (import: {str(e)})")
                print(f"   ❌ ÉCHEC IMPORT: {e}")
                continue
            
            # Étape 2.2: Analyse du module
            print(f"\n   ÉTAPE 2: Analyse du module")
            print(f"   {'-'*40}")
            
            agent_class_name = analyze_agent_module_verbose(module, agent_dir)
            if not agent_class_name:
                stats['failed_init'] += 1
                failed_imports.append(f"{agent_dir} (aucune classe Agent)")
                continue
            
            # Étape 2.3: Création de l'instance
            print(f"\n   ÉTAPE 3: Création de l'instance")
            print(f"   {'-'*40}")
            
            try:
                agent_class = getattr(module, agent_class_name)
                
                # Chercher le fichier de config
                config_file = os.path.join(agent_path, "config.yaml")
                print(f"      Configuration: {config_file}")
                
                if os.path.exists(config_file):
                    print(f"      ✓ Fichier trouvé")
                    agent = agent_class(config_file)
                    print(f"      ✓ Instance créée avec config")
                else:
                    print(f"      ⚠️ Fichier non trouvé")
                    try:
                        agent = agent_class()
                        print(f"      ✓ Instance créée sans config")
                        warnings.append("config_manquante")
                    except TypeError:
                        agent = agent_class(None)
                        print(f"      ✓ Instance créée avec config=None")
                        warnings.append("config_par_defaut")
                
                print(f"      📦 Type: {type(agent).__name__}")
                
            except Exception as e:
                stats['failed_init'] += 1
                failed_imports.append(f"{agent_dir} (instanciation: {str(e)})")
                print(f"      ❌ Erreur: {e}")
                print(f"      {traceback.format_exc().split(chr(10))[-2]}")
                continue
            
            # Étape 2.4: Initialisation
            print(f"\n   ÉTAPE 4: Initialisation")
            print(f"   {'-'*40}")
            
            try:
                if hasattr(agent, 'initialize') and callable(agent.initialize):
                    print(f"      ✓ Méthode initialize() trouvée")
                    
                    if inspect.iscoroutinefunction(agent.initialize):
                        print(f"      ✓ Méthode asynchrone détectée")
                        await agent.initialize()
                    else:
                        print(f"      ✓ Méthode synchrone détectée")
                        agent.initialize()
                    
                    print(f"      ✓ Initialisation réussie")
                else:
                    print(f"      ⚠️ Pas de méthode initialize()")
                    warnings.append("pas_initialize")
                
                # Vérifier les attributs essentiels
                print(f"\n   ÉTAPE 5: Vérification des attributs")
                print(f"   {'-'*40}")
                
                if hasattr(agent, 'name'):
                    print(f"      ✓ name: {agent.name}")
                else:
                    print(f"      ⚠️ name manquant")
                    try:
                        agent.name = agent_dir
                        warnings.append("name_manquant")
                    except:
                        pass
                
                if hasattr(agent, 'status'):
                    print(f"      ✓ status: {agent.status}")
                else:
                    print(f"      ⚠️ status manquant")
                    try:
                        agent.status = "ready"
                        warnings.append("status_manquant")
                    except:
                        pass
                
                if hasattr(agent, 'version'):
                    print(f"      ✓ version: {agent.version}")
                
                # Stocker l'agent
                agents[agent_dir] = agent
                
                if warnings:
                    stats['partial'] += 1
                    print(f"\n   ⚠️ AGENT CHARGÉ AVEC AVERTISSEMENTS: {', '.join(warnings)}")
                else:
                    stats['initialized'] += 1
                    print(f"\n   ✅ AGENT CHARGÉ AVEC SUCCÈS!")
                
            except Exception as e:
                stats['failed_init'] += 1
                failed_imports.append(f"{agent_dir} (init: {str(e)})")
                print(f"      ❌ Erreur initialisation: {e}")
                print(f"      {traceback.format_exc().split(chr(10))[-2]}")
            
        except Exception as e:
            stats['failed_init'] += 1
            failed_imports.append(f"{agent_dir} (inconnu: {str(e)})")
            print(f"   ❌ Erreur inattendue: {e}")
            print(f"      {traceback.format_exc().split(chr(10))[-3:]}")
    
    # Étape 3: Charger les sous-agents (si nécessaire)
    if structure['sous_agents']:
        print("\n" + "="*80)
        print("📦 CHARGEMENT DES SOUS-AGENTS")
        print("="*80)
        
        for parent_agent, subagents in structure['sous_agents'].items():
            for subagent_dir, subagent_info in subagents.items():
                print(f"\n{'='*60}")
                print(f"📦 SOUS-AGENT: {parent_agent}.{subagent_dir}")
                print(f"{'='*60}")
                
                # Note: Les sous-agents sont généralement chargés par leur parent
                # On ne les charge pas directement ici
                print(f"   ℹ️  Les sous-agents sont normalement chargés par leur agent parent")
                print(f"   📁 Chemin: {subagent_info['path']}")
                print(f"   📄 Fichiers: {', '.join(subagent_info['files']['list'])}")
    
    # Afficher les statistiques finales
    print("\n" + "="*80)
    print("📊 STATISTIQUES FINALES DU CHARGEMENT")
    print("="*80)
    print(f"📦 Agents principaux trouvés: {stats['total_agents']}")
    print(f"📦 Sous-agents trouvés: {stats['total_sous_agents']}")
    print(f"📦 Tentative de chargement: {stats['total_agents']}")
    print(f"✅ Agents complètement initialisés: {stats['initialized']}")
    print(f"⚠️ Agents partiellement chargés: {stats['partial']}")
    print(f"❌ Échecs import: {stats['failed_import']}")
    print(f"❌ Échecs initialisation: {stats['failed_init']}")
    
    if agents:
        print(f"\n✅ Agents disponibles ({len(agents)}):")
        # Trier par statut
        fully_ready = []
        partial = []
        
        for name, agent in agents.items():
            agent_name = getattr(agent, 'name', name)
            agent_status = getattr(agent, 'status', 'unknown')
            status_emoji = "✅" if agent_status == "ready" else "⚠️"
            
            if agent_status == "ready":
                fully_ready.append(f"   {status_emoji} {name:20} -> {agent_name} [{agent_status}]")
            else:
                partial.append(f"   {status_emoji} {name:20} -> {agent_name} [{agent_status}]")
        
        if fully_ready:
            print("\n   --- Agents complets ---")
            for line in fully_ready:
                print(line)
        
        if partial:
            print("\n   --- Agents partiels ---")
            for line in partial:
                print(line)
    else:
        print(f"\n⚠️ Aucun agent chargé")
    
    if failed_imports:
        print(f"\n❌ Détails des échecs ({len(failed_imports)}):")
        for fail in failed_imports[:10]:
            print(f"   • {fail}")
        if len(failed_imports) > 10:
            print(f"   ... et {len(failed_imports) - 10} autres")
    
    print("="*80)
    
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
            }
        ],
        "dependencies": [
            {"from": "SC_002", "to": "SC_001"},
            {"from": "BE_001", "to": "SC_001"},
            {"from": "FE_001", "to": "BE_001"},
            {"from": "DO_001", "to": "BE_001"},
            {"from": "DO_001", "to": "FE_001"},
            {"from": "DOC_001", "to": "*"},
            {"from": "SEC_001", "to": "SC_001"},
            {"from": "SEC_001", "to": "SC_002"},
            {"from": "SEC_001", "to": "BE_001"},
            {"from": "MON_001", "to": "DO_001"}
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
    print("\n" + "="*80)
    print("🚀 TEST COMPLET ULTRA-VERBOSE DE TOUS LES AGENTS")
    print("="*80 + "\n")
    
    # Menu de diagnostic
    print("Options de diagnostic:")
    print("1. 🔍 Scan uniquement (structure des dossiers)")
    print("2. 🚀 Chargement complet des agents")
    print("3. 🧪 Exécution du sprint")
    print("4. 🔬 Mode DEBUG complet (tout)")
    
    choice = input("\n👉 Votre choix (1-4): ").strip()
    
    if choice == "1":
        # Scan uniquement
        structure = scan_all_agents_and_subagents_verbose()
        print(f"\n✅ Scan terminé - {structure['stats']['total_agents']} agents trouvés")
        return
    
    elif choice == "2":
        # Chargement uniquement
        agents = await load_all_agents_verbose()
        print(f"\n✅ Chargement terminé - {len(agents)} agents chargés")
        return
    
    elif choice == "3":
        # Exécution du sprint
        print("\n📋 Création de la spécification...")
        spec_file = create_comprehensive_sprint_spec()
        
        print("\n🚀 Chargement des agents...")
        agents = await load_all_agents_verbose()
        
        if 'orchestrator' not in agents:
            print("\n❌ Orchestrator non disponible - arrêt du test")
            return
        
        orchestrator = agents['orchestrator']
        
        print("\n🚀 Lancement du sprint complet...")
        report = await orchestrator.execute_sprint(spec_file)
        
        print(f"\n" + "="*70)
        print(f"✅ SPRINT TERMINÉ")
        print(f"📊 Fragments: {report['metrics']['total_fragments']}")
        print(f"📈 Succès: {report['metrics']['success_rate']:.1f}%")
        
        if 'failed_fragments' in report['metrics'] and report['metrics']['failed_fragments']:
            failed = report['metrics']['failed_fragments']
            print(f"\n❌ Fragments en échec ({len(failed)}):")
            for f in failed:
                print(f"   • {f}")
        
        if 'recommendations' in report:
            print(f"\n💡 Recommandations:")
            for rec in report['recommendations']:
                print(f"   • {rec}")
    
    else:
        # Mode DEBUG complet
        print("\n🔬 MODE DEBUG COMPLET - Tout sera exécuté")
        
        # Scan
        structure = scan_all_agents_and_subagents_verbose()
        
        # Chargement
        agents = await load_all_agents_verbose()
        
        # Sprint si orchestrator disponible
        if 'orchestrator' in agents:
            spec_file = create_comprehensive_sprint_spec()
            report = await agents['orchestrator'].execute_sprint(spec_file)
            print(f"\n📊 Résultat sprint: {report['metrics']['success_rate']:.1f}%")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(main())