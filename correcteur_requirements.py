# correcteur_requirements.py
import os

print("🔧 Correction de requirements.txt")
print("=" * 40)

requirements_path = "requirements.txt"

# Nouvelles dépendances corrigées
new_requirements = '''# Dépendances du projet SmartContractDevPipeline
# NOTE: python>=3.9 n'est pas une dépendance pip, c'est une exigence système

# Core
PyYAML>=6.0
pydantic>=2.5.0
python-dotenv>=1.0.0

# Async
aiohttp>=3.9.0

# Web3 & Blockchain
web3>=6.0.0
eth-account>=0.11.0
eth-typing>=3.0.0

# Development (optionnel)
black>=23.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0

# API (optionnel)
fastapi>=0.104.0
uvicorn>=0.24.0
httpx>=0.25.0

# Utils (optionnel)
jinja2>=3.1.0
rich>=13.0.0
'''

# Vérifier si le fichier existe
if os.path.exists(requirements_path):
    with open(requirements_path, 'r', encoding='utf-8') as f:
        old_content = f.read()
    
    print("📄 Ancien contenu de requirements.txt:")
    print("-" * 40)
    print(old_content[:200] + "..." if len(old_content) > 200 else old_content)
    print("-" * 40)
    
    # Sauvegarder l'ancienne version
    backup_path = requirements_path + ".backup"
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(old_content)
    
    print(f"💾 Backup créé: {backup_path}")

# Écrire la nouvelle version
with open(requirements_path, 'w', encoding='utf-8') as f:
    f.write(new_requirements)

print("✅ requirements.txt corrigé")
print("\n📋 Nouvelles dépendances:")
print("-" * 40)
print(new_requirements)
print("-" * 40)

print("\n🎯 Installation des dépendances principales:")
print("pip install PyYAML aiohttp pydantic python-dotenv web3")

print("\n🎯 Installation complète (optionnel):")
print("pip install -r requirements.txt")