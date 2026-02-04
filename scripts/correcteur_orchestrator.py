# correcteur_orchestrator.py
import os
import sys

print("🔧 Correction de l'orchestrateur")
print("=" * 50)

# Chemin du fichier orchestrator
orchestrator_path = os.path.join("orchestrator", "orchestrator.py")
backup_path = orchestrator_path + ".backup"

# Lire le fichier
with open(orchestrator_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"📄 Lecture de {orchestrator_path}")

# Sauvegarder
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"💾 Backup créé: {backup_path}")

# Trouver la méthode initialize_agents
if "async def initialize_agents(self):" in content:
    print("✅ Méthode initialize_agents trouvée")
    
    # Nouvelle version corrigée de la méthode
    new_initialize_method = '''    async def initialize_agents(self):
        """Initialise tous les agents du pipeline"""
        if self.initialized:
            return
        
        self.logger.info("Initialisation des agents...")
        
        # Définir le chemin du projet pour les imports
        import os
        import sys
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # Dynamiquement importer les agents basés sur la config
        agents_to_load = self.config.get("agents", {})
        
        for agent_name, agent_config in agents_to_load.items():
            if agent_config.get("enabled", True):
                try:
                    # Construction du chemin d'import
                    module_path = agent_config.get("module", f"agents.{agent_name}.agent")
                    agent_class_name = agent_config.get("class", f"{agent_name.capitalize()}Agent")
                    
                    # Import dynamique simplifié
                    module_parts = module_path.split('.')
                    
                    try:
                        # Essayer d'importer directement
                        exec(f"from {module_path} import {agent_class_name}")
                        agent_class = eval(agent_class_name)
                    except:
                        # Méthode alternative avec importlib
                        import importlib
                        module_name = '.'.join(module_parts[:-1])
                        class_name = module_parts[-1]
                        
                        if module_name:
                            module = importlib.import_module(module_name)
                        else:
                            module = importlib.import_module(agent_name)
                        
                        agent_class = getattr(module, agent_class_name)
                    
                    # Instanciation
                    config_path = agent_config.get("config_path", "")
                    agent_instance = agent_class(config_path)
                    self.agents[agent_name] = agent_instance
                    
                    self.logger.info(f"✅ Agent {agent_name} initialisé")
                    
                except Exception as e:
                    self.logger.error(f"❌ Erreur lors de l'initialisation de {agent_name}: {e}")
                    import traceback
                    self.logger.error(traceback.format_exc())
        
        self.initialized = True
        self.logger.info(f"✅ {len(self.agents)} agents initialisés")'''
    
    # Remplacer l'ancienne méthode
    import re
    pattern = r'async def initialize_agents\(self\):(?s:.*?)(?=\n    async def|\n    def|\n\n|$)'
    
    # Essayer de remplacer
    new_content, count = re.subn(pattern, new_initialize_method, content)
    
    if count > 0:
        print("✅ Méthode initialize_agents remplacée")
        
        # Écrire le fichier corrigé
        with open(orchestrator_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ {orchestrator_path} corrigé")
        
        # Afficher un extrait de la correction
        print("\n📋 Extrait de la correction:")
        print("-" * 40)
        lines = new_initialize_method.split('\n')[:15]
        for line in lines:
            print(line)
        print("...")
        print("-" * 40)
        
    else:
        print("❌ Impossible de trouver/replacer la méthode")
        # Essayer une autre méthode
        lines = content.split('\n')
        new_lines = []
        in_method = False
        
        for line in lines:
            if line.strip() == "async def initialize_agents(self):":
                in_method = True
                new_lines.append(line)
                # Ajouter notre nouvelle méthode
                new_lines.extend(new_initialize_method.split('\n')[1:])
            elif in_method and line.startswith("    async def") and line != "    async def initialize_agents(self):":
                in_method = False
                new_lines.append(line)
            elif not in_method:
                new_lines.append(line)
        
        with open(orchestrator_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        print("✅ Correction appliquée (méthode alternative)")
        
else:
    print("❌ Méthode initialize_agents non trouvée")

# Vérifier aussi le début du fichier pour ajouter les imports nécessaires
print("\n🔍 Vérification des imports...")

if "import importlib" not in content:
    print("⚠️  importlib manquant, ajout...")
    
    # Ajouter importlib après les autres imports
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        if line.startswith("import ") and "importlib" not in line and i+1 < len(lines) and not lines[i+1].startswith("import "):
            new_lines.append("import importlib")
    
    with open(orchestrator_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("✅ importlib ajouté")

print("\n" + "=" * 50)
print("🎯 Testez maintenant:")
print("python orchestrator/orchestrator.py --test")
print("\n🔧 Si ça ne marche toujours pas, essayez:")
print("python test_simple.py")