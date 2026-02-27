import os
import yaml
from pathlib import Path

def unify_yaml_format(file_path):
    """Convertit un fichier YAML au format unifié (name + description)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    modified = False
    
    # Traiter les capacités
    if 'capabilities' in data:
        caps = data['capabilities']
        if caps and isinstance(caps, list):
            new_caps = []
            for cap in caps:
                if isinstance(cap, str):
                    new_caps.append({
                        'name': cap,
                        'description': f'Capacité {cap.lower().replace("_", " ")}'
                    })
                    modified = True
                else:
                    new_caps.append(cap)
            if modified:
                data['capabilities'] = new_caps
    
    # Sauvegarder si modifié
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        print(f"✅ Converti: {file_path}")
    
    return modified

# Parcourir tous les fichiers config.yaml
for config_file in Path('.').rglob('config.yaml'):
    unify_yaml_format(config_file)