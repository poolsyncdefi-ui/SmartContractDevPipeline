import os
import yaml
from pathlib import Path

def convert_orchestrator_config(file_path):
    """Convertit le fichier orchestrator/config.yaml au format standard agent"""
    
    print(f"🔄 Conversion de {file_path}...")
    
    # Lire le fichier existant
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    # Créer la nouvelle structure standard
    standard_format = {
        'agent': {
            'name': 'Orchestrateur',
            'display_name': 'Orchestrateur de Workflows',
            'version': data.get('orchestrator', {}).get('version', '1.0.0'),
            'description': 'Orchestration globale des workflows et sprints du pipeline',
            'agent_type': 'concrete',
            'enabled': True,
            'instantiate': True,
            'dependencies': ['base_agent'],
            'initialization_order': 15,
            'parent': 'base_agent',
            'purpose': 'Orchestration des workflows complexes entre agents',
            'specialization': 'workflow_orchestration',
            'mandatory': True,
            
            # Capacités standards de l'orchestrateur
            'capabilities': [
                {
                    'name': 'WORKFLOW_ORCHESTRATION',
                    'description': 'Orchestration de workflows complexes'
                },
                {
                    'name': 'SPRINT_MANAGEMENT',
                    'description': 'Gestion de sprints et planification'
                },
                {
                    'name': 'TASK_SCHEDULING',
                    'description': 'Planification et ordonnancement des tâches'
                },
                {
                    'name': 'RESOURCE_ALLOCATION',
                    'description': 'Allocation et gestion des ressources'
                },
                {
                    'name': 'DEADLINE_MANAGEMENT',
                    'description': 'Gestion des délais et échéances'
                },
                {
                    'name': 'PARALLEL_EXECUTION',
                    'description': 'Exécution parallèle de workflows'
                },
                {
                    'name': 'DEPENDENCY_RESOLUTION',
                    'description': 'Résolution des dépendances entre tâches'
                },
                {
                    'name': 'STATE_TRACKING',
                    'description': 'Suivi d\'état des workflows'
                }
            ]
        },
        
        # Conserver les workflows comme sous-agents
        'subAgents': []
    }
    
    # Convertir les workflows en sous-agents
    if 'workflow' in data:
        for wf_name, wf_config in data['workflow'].items():
            # Créer un sous-agent pour chaque workflow
            sub_agent = {
                'id': f"workflow_{wf_name}",
                'name': wf_config.get('name', wf_name),
                'display_name': wf_config.get('name', wf_name),
                'description': wf_config.get('description', f'Workflow {wf_name}'),
                'version': '1.0.0',
                'enabled': True,
                'config_path': None,  # Pas de fichier de config séparé
                'dependencies': [],
                
                # Capacités basées sur les étapes du workflow
                'capabilities': [
                    {
                        'name': f"STEP_{step.get('id', f'step_{i}')}".upper(),
                        'description': f"Étape: {step.get('task', 'unknown')}"
                    }
                    for i, step in enumerate(wf_config.get('steps', []))
                ]
            }
            standard_format['subAgents'].append(sub_agent)
    
    # Conserver aussi la configuration des autres agents si présente
    if 'agents' in data:
        standard_format['managed_agents'] = data['agents']
    
    # Sauvegarder le fichier converti
    backup_path = file_path.with_suffix('.yaml.backup')
    os.rename(file_path, backup_path)
    print(f"  ✅ Backup créé: {backup_path}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(standard_format, f, allow_unicode=True, sort_keys=False, indent=2)
    
    print(f"  ✅ Fichier converti avec succès: {file_path}")
    print(f"  📊 {len(standard_format['subAgents'])} workflows convertis en sous-agents")
    
    return True

def main():
    # Chemin vers le fichier orchestrator/config.yaml
    orchestrator_config = Path(__file__).parent / 'orchestrator' / 'config.yaml'
    
    if not orchestrator_config.exists():
        print(f"❌ Fichier non trouvé: {orchestrator_config}")
        return
    
    convert_orchestrator_config(orchestrator_config)
    
    print("\n✨ Conversion terminée !")
    print("Le fichier orchestrator/config.yaml est maintenant au format standard.")
    print("Les workflows sont maintenant des sous-agents de l'orchestrateur.")

if __name__ == "__main__":
    main()