#!/usr/bin/env python3
"""
Share GitHub V9.7 - Version FINALE avec corrections
Génération de PROJECT_SHARE.txt et upload vers GitHub Gists
Affichage simplifié des liens
"""

import json
import os
import sys
import datetime
import math
import fnmatch
import subprocess  # ← IMPORT AJOUTÉ
from pathlib import Path
import requests

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    def __init__(self):
        current_dir = Path.cwd()
        
        # Déterminer les chemins
        if current_dir.name == "SmartContractDevPipeline":
            self.project_root = current_dir
            self.parent_dir = current_dir.parent
        else:
            self.project_root = current_dir / "SmartContractDevPipeline"
            self.parent_dir = current_dir
        
        # Chercher la config dans le dossier parent
        self.config_path = self.parent_dir / "project_config.json"
        self.config = self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis project_config.json"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✓ Configuration: {self.config_path}")
                return config
            except Exception as e:
                print(f"⚠ Erreur lecture config: {e}")
        
        print("⚠ Utilisation configuration par défaut")
        return {
            "PROJECT_NAME": "SmartContractDevPipeline",
            "GITHUB_TOKEN": "",
            "PROJECT_PATH": str(self.project_root),
            "MAX_GIST_SIZE_MB": 45,
            "EXCLUDE_PATTERNS": [
                "node_modules/*", ".git/*", "__pycache__/*", ".venv/*", "venv/*", "env/*",
                "dist/*", "build/*", ".next/*", ".nuxt/*", "target/*", ".gradle/*",
                ".vscode/*", ".idea/*", ".vs/*", ".pytest_cache/*", ".mypy_cache/*",
                ".coverage/*", ".tox/*", "logs/*", ".cache/*", ".tmp/*", "temp/*",
                ".yarn/*", ".npm/*", "bower_components/*", "jspm_packages/*",
                ".serverless/*", ".webpack/*", ".angular/*", ".vuepress/*", ".docusaurus/*",
                ".sapper/*", ".gatsby/*", ".gridsome/*", ".quasar/*", ".ionic/*", ".expo/*",
                ".react-native/*", ".meteor/*", ".electron/*", ".github/*", ".gitlab/*",
                ".circleci/*", ".travis/*", ".appveyor/*", ".DS_Store", "Thumbs.db",
                "desktop.ini", "Icon", "$RECYCLE.BIN/*", "System Volume Information/*",
                ".Spotlight-V100/*", ".Trashes/*", ".TemporaryItems/*", ".fseventsd/*",
                ".DocumentRevisions-V100/*", "package-lock.json", "yarn.lock",
                "pnpm-lock.yaml", "shrinkwrap.json", "*.log", "*.tmp", "*.cache",
                "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dylib", "*.dll", "*.exe",
                "*.class", "*.jar", "*.o", "*.obj", ".env*", "*.key", "*.pem",
                "*.crt", "*.cert", "*.p12", "*.pfx", "*.keystore",
                "PROJECT_SHARE.txt"
            ],
            "EXCLUDE_DIRS": [
                "node_modules", ".git", ".vscode", ".idea", ".vs", "__pycache__",
                ".pytest_cache", ".mypy_cache", ".coverage", ".tox", "venv",
                ".venv", "env", "virtualenv", "env.bak", "dist", "build", "out",
                ".next", ".nuxt", "target", ".gradle", ".settings", "coverage",
                ".nyc_output", "logs", ".cache", ".tmp", "temp", "tmp", ".yarn",
                ".npm", "bower_components", "jspm_packages", ".serverless",
                ".webpack", ".angular", ".vuepress", ".docusaurus", ".sapper",
                ".gatsby", ".gridsome", ".quasar", ".ionic", ".expo",
                ".react-native", ".meteor", ".electron", ".github", ".gitlab",
                ".circleci", ".travis", ".appveyor", "$RECYCLE.BIN",
                "System Volume Information", ".Spotlight-V100", ".Trashes",
                ".TemporaryItems", ".fseventsd", ".DocumentRevisions-V100",
                ".gists", "gists", "github_gists", "test_gists", "gist_test",
                ".gist_cache", ".github_cache"
            ],
            "INCLUDE_PATTERNS": [
                "*.py", "*.js", "*.ts", "*.sol", "*.rs", "*.go", "*.java",
                "*.cpp", "*.h", "*.hpp", "*.c", "*.cs", "*.rb", "*.php",
                "*.swift", "*.kt", "*.kts", "*.scala", "*.md", "*.txt",
                "*.json", "*.yaml", "*.yml", "*.toml", "*.ini", "*.cfg",
                "*.conf", "*.html", "*.css", "*.scss", "*.sass", "*.less",
                "*.mermaid", "*.svg", "*.sh", "*.bat", "*.ps1", "*.dockerfile",
                "Dockerfile*", "docker-compose*", "Makefile", "Gemfile",
                "Cargo.toml", "go.mod", "package.json", "requirements.txt",
                "pyproject.toml", "setup.py", "*.sql", "*.graphql", "*.gql"
            ]
        }
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def save_token(self, token):
        self.config["GITHUB_TOKEN"] = token
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            return True
        except:
            return False


# ============================================================================
# FILTRAGE
# ============================================================================

def should_exclude(path, config):
    """Vérifie si un chemin doit être exclu"""
    path_str = str(path)
    path_parts = path.parts
    
    # Dossiers exclus
    exclude_dirs = config.get("EXCLUDE_DIRS", [])
    for part in path_parts:
        if part in exclude_dirs:
            return True
    
    # Patterns d'exclusion
    exclude_patterns = config.get("EXCLUDE_PATTERNS", [])
    for pattern in exclude_patterns:
        if pattern.endswith('/*'):
            dir_pattern = pattern[:-2]
            if f"{dir_pattern}{os.sep}" in path_str or f"{dir_pattern}/" in path_str:
                return True
        elif fnmatch.fnmatch(path.name, pattern):
            return True
        elif fnmatch.fnmatch(path_str, pattern):
            return True
    
    return False

def should_include(path, config):
    """Vérifie si un fichier doit être inclus"""
    if path.is_dir():
        return False
    
    include_patterns = config.get("INCLUDE_PATTERNS", ["*"])
    for pattern in include_patterns:
        if fnmatch.fnmatch(path.name, pattern):
            return True
    
    return False

def collect_files(project_path, config):
    """Collecte les fichiers du projet"""
    all_files = []
    project_root = Path(project_path)
    
    if not project_root.exists():
        print(f"✗ Chemin introuvable: {project_path}")
        return []
    
    for root, dirs, files in os.walk(project_root):
        # Filtrer les dossiers
        dirs[:] = [d for d in dirs if not should_exclude(Path(root) / d, config)]
        
        for file in files:
            file_path = Path(root) / file
            
            if should_exclude(file_path, config):
                continue
            
            if should_include(file_path, config):
                all_files.append(file_path)
    
    return sorted(all_files)


# ============================================================================
# LECTURE DE FICHIERS
# ============================================================================

def read_file_with_line_numbers(file_path):
    """Lit un fichier et retourne son contenu avec numéros de lignes"""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            numbered_lines = []
            for i, line in enumerate(lines, 1):
                line = line.rstrip('\n\r')
                numbered_lines.append(f"   {i:4d}: {line}")
            
            return numbered_lines
        except:
            continue
    
    return [f"   [FICHIER BINAIRE]"]


# ============================================================================
# GÉNÉRATION DE PROJECT_SHARE.txt
# ============================================================================

def create_full_share(config):
    """Crée PROJECT_SHARE.txt avec les fichiers du projet"""
    print("\n" + "="*60)
    print("GÉNÉRATION DE PROJECT_SHARE.txt")
    print("="*60)
    
    project_path = config.get("PROJECT_PATH")
    if not project_path:
        print("✗ PROJECT_PATH non défini")
        return False
    
    project_root = Path(project_path)
    if not project_root.exists():
        print(f"✗ Chemin introuvable: {project_path}")
        return False
    
    print("Scan du projet...")
    files = collect_files(project_path, config)
    
    if not files:
        print("✗ Aucun fichier trouvé")
        return False
    
    output_file = project_root / "PROJECT_SHARE.txt"
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"Création de {output_file.name}...")
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # En-tête
        out_f.write(f"PROJECT: {config.get('PROJECT_NAME')}\n")
        out_f.write(f"DATE: {timestamp}\n")
        out_f.write(f"FILES: {len(files)}\n")
        out_f.write("=" * 80 + "\n\n")
        
        # Fichiers
        for file_path in files:
            out_f.write(f"FICHIER : {file_path}\n")
            
            numbered_lines = read_file_with_line_numbers(file_path)
            for line in numbered_lines:
                out_f.write(line + '\n')
            
            out_f.write('\n')
    
    if output_file.exists():
        file_size = output_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n✅ Fichier créé: {output_file.name}")
        print(f"📊 {len(files)} fichiers - {file_size_mb:.2f} MB")
        return True
    else:
        print("❌ Échec de la création")
        return False


# ============================================================================
# FONCTIONS POUR GISTS
# ============================================================================

def estimate_gist_size(content):
    return len(content.encode('utf-8'))

def split_files_into_gists(project_root, config):
    """
    Divise les fichiers du projet en Gists sans inclure PROJECT_SHARE.txt
    """
    all_files = collect_files(project_root, config)
    
    # Exclure PROJECT_SHARE.txt explicitement
    all_files = [f for f in all_files if f.name != "PROJECT_SHARE.txt"]
    
    max_size_bytes = config.get("MAX_GIST_SIZE_MB", 45) * 1024 * 1024
    
    # Calculer la taille de chaque fichier
    file_sizes = []
    for file_path in all_files:
        content = '\n'.join(read_file_with_line_numbers(file_path))
        size = estimate_gist_size(content)
        file_sizes.append({
            "path": str(file_path),
            "name": file_path.name,
            "size": size,
            "content": content
        })
    
    # Trier par taille (plus gros d'abord)
    file_sizes.sort(key=lambda x: x["size"], reverse=True)
    
    # Algorithme de bin packing
    gist_parts = []
    current_gist = {"index": 1, "files": [], "size": 0}
    
    for file_info in file_sizes:
        if current_gist["size"] + file_info["size"] > max_size_bytes and current_gist["files"]:
            gist_parts.append(current_gist)
            current_gist = {"index": len(gist_parts) + 1, "files": [], "size": 0}
        
        current_gist["files"].append(file_info)
        current_gist["size"] += file_info["size"]
    
    if current_gist["files"]:
        gist_parts.append(current_gist)
    
    return gist_parts

def create_gist_content(gist_data, part_index, total_parts, project_name):
    """Crée le contenu d'un Gist"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    content = []
    content.append("=" * 80)
    content.append(f"PROJECT_SHARE - PARTIE {part_index}/{total_parts}")
    content.append(f"Projet: {project_name}")
    content.append(f"Date: {timestamp}")
    content.append(f"Fichiers: {len(gist_data['files'])}")
    content.append("=" * 80)
    content.append("")
    
    for file_info in gist_data["files"]:
        content.append("")
        content.append(f"FICHIER : {file_info['path']}")
        content.extend(file_info["content"].split('\n'))
        content.append("")
    
    return '\n'.join(content)

def upload_gists_to_github(gist_parts, config, project_root):
    """Upload les Gists sans confirmation"""
    print("\n" + "="*60)
    print("UPLOAD VERS GITHUB GISTS")
    print("="*60)
    
    github_token = config.get("GITHUB_TOKEN")
    if not github_token:
        print("\n🔑 Token GitHub requis")
        github_token = input("Collez votre token GitHub: ").strip()
        if not github_token:
            print("✗ Token requis")
            return None
        config.save_token(github_token)
    
    headers = {"Authorization": f"token {github_token}"}
    
    try:
        test_response = requests.get("https://api.github.com/user", headers=headers)
        if test_response.status_code == 200:
            user = test_response.json().get('login')
            print(f"✓ Connecté: {user}")
        else:
            print(f"✗ Token invalide")
            return None
    except:
        print(f"✗ Erreur connexion")
        return None
    
    uploaded_gists = []
    total_size_mb = 0
    
    print(f"\n🚀 Création de {len(gist_parts)} Gist(s)...")
    
    for i, gist_data in enumerate(gist_parts):
        part_index = i + 1
        total_parts = len(gist_parts)
        size_mb = gist_data["size"] / (1024 * 1024)
        total_size_mb += size_mb
        
        content = create_gist_content(gist_data, part_index, total_parts, config.get('PROJECT_NAME'))
        filename = f"PROJECT_PART{part_index:02d}_of_{total_parts:02d}.txt"
        
        data = {
            "description": f"{config.get('PROJECT_NAME')} - Partie {part_index}/{total_parts}",
            "public": True,
            "files": {filename: {"content": content}}
        }
        
        try:
            response = requests.post("https://api.github.com/gists", headers=headers, json=data, timeout=120)
            
            if response.status_code == 201:
                gist_response = response.json()
                gist_url = gist_response["html_url"]
                
                print(f"  ✅ Partie {part_index}/{total_parts} - {gist_url}")
                
                uploaded_gists.append({
                    "part": part_index,
                    "url": gist_url,
                    "size_mb": round(size_mb, 2),
                    "files": len(gist_data["files"])
                })
                
            else:
                print(f"  ❌ Erreur part {part_index}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ Exception part {part_index}: {e}")
    
    if uploaded_gists:
        print(f"\n📊 RÉCAPITULATIF:")
        for gist in uploaded_gists:
            print(f"  Partie {gist['part']:02d}: {gist['url']} ({gist['size_mb']:.2f} MB)")
    
    return uploaded_gists

def save_gist_index(uploaded_gists, config, project_root):
    """Sauvegarde l'index des Gists dans un fichier"""
    if not uploaded_gists:
        return
    
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    index_file = project_root / "GISTS_INDEX.txt"
    
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write(f"INDEX DES GISTS - {config.get('PROJECT_NAME')}\n")
        f.write("="*80 + "\n")
        f.write(f"Date: {timestamp}\n")
        f.write(f"Total Gists: {len(uploaded_gists)}\n")
        f.write(f"Taille totale: {sum(g['size_mb'] for g in uploaded_gists):.2f} MB\n")
        f.write("-"*80 + "\n\n")
        
        for gist in sorted(uploaded_gists, key=lambda x: x['part']):
            f.write(f"Partie {gist['part']:02d}: {gist['url']}\n")
        
        f.write("\n" + "="*80 + "\n")
    
    print(f"\n📄 Index sauvegardé: {index_file.name}")

def share_to_github_gists(config, project_root):
    """Partage les fichiers du projet sur GitHub Gists"""
    print("\n" + "="*60)
    print("SHARE TO GITHUB GISTS")
    print("="*60)
    
    print("Analyse des fichiers du projet...")
    gist_parts = split_files_into_gists(str(project_root), config)
    
    if not gist_parts:
        print("✗ Aucun fichier à partager")
        return False
    
    total_files = sum(len(p['files']) for p in gist_parts)
    total_size = sum(p['size'] for p in gist_parts) / (1024 * 1024)
    
    print(f"📊 {total_files} fichiers - {total_size:.2f} MB - {len(gist_parts)} Gist(s)")
    
    uploaded = upload_gists_to_github(gist_parts, config, project_root)
    
    if uploaded:
        save_gist_index(uploaded, config, project_root)
        print("\n✅ PARTAGE TERMINÉ")
        return True
    else:
        print("\n❌ Aucun Gist créé")
        return False


# ============================================================================
# GIT COMMIT + PUSH
# ============================================================================

def git_commit_push_publish(config, project_root):
    """Commit et push Git"""
    print("\n" + "="*60)
    print("GIT COMMIT + PUSH")
    print("="*60)
    
    try:
        # Vérifier si on est dans un repo Git
        subprocess.run(["git", "status"], check=True, capture_output=True, text=True, cwd=project_root)
        
        # Voir les changements
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=project_root)
        
        if not status.stdout.strip():
            print("ℹ Aucun changement à commiter")
            return True
        
        # Afficher les fichiers modifiés
        files_changed = len(status.stdout.strip().split('\n'))
        print(f"📝 {files_changed} fichier(s) modifié(s)")
        
        # Message de commit
        default_msg = f"Mise à jour {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        commit_msg = input(f"\nMessage commit (défaut: {default_msg}): ").strip() or default_msg
        
        # Git add
        print("📦 Ajout des fichiers...")
        subprocess.run(["git", "add", "."], cwd=project_root, check=True)
        
        # Git commit
        print("📝 Création du commit...")
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=project_root, check=True)
        
        # Git push
        print("☁ Push vers GitHub...")
        branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=project_root)
        current_branch = branch.stdout.strip() or "main"
        
        result = subprocess.run(["git", "push", "origin", current_branch], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print("✓ Push réussi")
            return True
        else:
            print("✗ Échec du push")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"✗ Erreur Git: {e}")
        return False
    except FileNotFoundError:
        print("✗ Git non installé")
        return False


# ============================================================================
# MENU PRINCIPAL
# ============================================================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu(config, project_root):
    while True:
        clear_screen()
        print("\n" + "="*60)
        print(f"SHARE GITHUB V9.7 - {config.get('PROJECT_NAME')}")
        print("="*60)
        print(f"Projet: {project_root}")
        print(f"Config: {config.config_path}")
        print("\n" + "="*60)
        print("1. GÉNÉRER PROJECT_SHARE.txt")
        print("2. GIT COMMIT + PUSH")
        print("3. SHARE TO GITHUB GISTS")
        print("4. EXIT")
        print("="*60)
        
        choice = input("\nChoix (1-4): ").strip()
        
        if choice == "1":
            create_full_share(config)
        elif choice == "2":
            git_commit_push_publish(config, project_root)
        elif choice == "3":
            share_to_github_gists(config, project_root)
        elif choice == "4":
            print("\nAu revoir!")
            break
        
        input("\nAppuyez sur ENTER...")


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    config = Config()
    
    try:
        main_menu(config, config.project_root)
    except KeyboardInterrupt:
        print("\n\nInterrompu.")
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()