import os
import yaml
from pathlib import Path

def find_sub_agents(agent_path):
    """Trouve tous les sous-agents dans le dossier sous_agents/ d'un agent"""
    sub_agents = []
    sous_agents_dir = agent_path / 'sous_agents'
    
    if not sous_agents_dir.exists():
        return sub_agents
    
    for sub_dir in sous_agents_dir.iterdir():
        if sub_dir.is_dir():
            config_file = sub_dir / 'config.yaml'
            if config_file.exists():
                # Lire la config du sous-agent pour obtenir son nom
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        sub_config = yaml.safe_load(f)
                    
                    # Extraire le nom du sous-agent
                    sub_name = None
                    if sub_config and 'sub_agent' in sub_config:
                        sub_name = sub_config['sub_agent'].get('name')
                    elif sub_config and 'agent' in sub_config:
                        sub_name = sub_config['agent'].get('name')
                    
                    sub_agents.append({
                        'id': sub_dir.name,
                        'name': sub_name or sub_dir.name.replace('_', ' ').title(),
                        'display_name': sub_name or sub_dir.name.replace('_', ' ').title(),
                        'config_path': f"agents/{agent_path.name}/sous_agents/{sub_dir.name}/config.yaml",
                        'dependencies': [agent_path.name]
                    })
                    print(f"    ✅ Sous-agent trouvé: {sub_dir.name}")
                except Exception as e:
                    print(f"    ⚠ Erreur lecture {sub_dir.name}: {e}")
    
    return sub_agents

def update_agent_config(agent_path):
    """Met à jour le fichier config.yaml d'un agent pour inclure ses sous-agents"""
    config_file = agent_path / 'config.yaml'
    
    if not config_file.exists():
        print(f"  ⚠ Fichier config.yaml non trouvé dans {agent_path}")
        return
    
    print(f"\n📝 Traitement de {agent_path.name}...")
    
    # Lire la config existante
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Chercher les sous-agents
    sub_agents = find_sub_agents(agent_path)
    
    if not sub_agents:
        print(f"  ℹ Aucun sous-agent trouvé pour {agent_path.name}")
        return
    
    print(f"  📦 {len(sub_agents)} sous-agent(s) trouvé(s)")
    
    # S'assurer que la structure agent existe
    if 'agent' not in config:
        config = {'agent': config}
    
    # Ajouter ou mettre à jour la section subAgents
    if 'subAgents' not in config['agent']:
        config['agent']['subAgents'] = []
    
    # Ajouter les nouveaux sous-agents (éviter les doublons)
    existing_ids = {sub['id'] for sub in config['agent']['subAgents']}
    
    for sub in sub_agents:
        if sub['id'] not in existing_ids:
            config['agent']['subAgents'].append(sub)
            print(f"    ✅ Ajouté: {sub['name']}")
    
    # Sauvegarder le fichier
    backup_file = config_file.with_suffix('.yaml.backup')
    if not backup_file.exists():
        os.rename(config_file, backup_file)
        print(f"  ✅ Backup créé: {backup_file.name}")
    
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False, indent=2)
    
    print(f"  ✅ Fichier mis à jour: {config_file.name}")

def main():
    # Chemin vers le dossier agents
    agents_dir = Path(__file__).parent / 'agents'
    
    if not agents_dir.exists():
        print(f"❌ Dossier agents/ non trouvé: {agents_dir}")
        return
    
    print("🚀 Démarrage de la mise à jour des configurations agents...")
    
    # Parcourir tous les sous-dossiers de agents/
    for agent_dir in agents_dir.iterdir():
        if agent_dir.is_dir() and not agent_dir.name.startswith('_'):
            # Ignorer certains dossiers si nécessaire
            if agent_dir.name in ['__pycache__', 'sous_agents']:
                continue
            
            update_agent_config(agent_dir)
    
    print("\n✨ Mise à jour terminée !")
    print("Les fichiers config.yaml ont maintenant leurs sous-agents déclarés.")

if __name__ == "__main__":
    main()