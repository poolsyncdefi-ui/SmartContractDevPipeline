#!/usr/bin/env python3
"""
Share GitHub V9.4 - Version FINALE
Génération de PROJECT_SHARE.txt et upload vers GitHub Gists
Configuration depuis D:\Web3Projects\project_config.json
"""

import json
import os
import sys
import datetime
import subprocess
import math
import fnmatch
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
        
        # Configuration par défaut
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
                "*.crt", "*.cert", "*.p12", "*.pfx", "*.keystore"
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

def parse_project_share_file(input_file):
    """Parse PROJECT_SHARE.txt pour récupérer la structure"""
    if not os.path.exists(input_file):
        return None
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return None
    
    lines = content.split('\n')
    
    # En-tête
    header = {"project": "", "date": "", "files_count": 0}
    for i in range(min(10, len(lines))):
        if lines[i].startswith("PROJECT: "):
            header["project"] = lines[i].replace("PROJECT: ", "").strip()
        elif lines[i].startswith("DATE: "):
            header["date"] = lines[i].replace("DATE: ", "").strip()
        elif lines[i].startswith("FILES: "):
            try:
                header["files_count"] = int(lines[i].replace("FILES: ", "").strip())
            except:
                pass
    
    # Fichiers
    file_contents = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("FICHIER : "):
            file_info = {
                "path": lines[i].replace("FICHIER : ", "").strip(),
                "content_lines": []
            }
            i += 1
            
            while i < len(lines) and not lines[i].startswith("FICHIER : "):
                if lines[i].strip():
                    file_info["content_lines"].append(lines[i])
                i += 1
            
            file_contents.append(file_info)
        else:
            i += 1
    
    return {"header": header, "files": file_contents}

def split_files_into_gists(parsed_data, config):
    """Divise les fichiers en Gists"""
    files = parsed_data["files"]
    max_size_bytes = config.get("MAX_GIST_SIZE_MB", 45) * 1024 * 1024
    
    file_sizes = []
    for file_info in files:
        content = '\n'.join(file_info["content_lines"])
        size = estimate_gist_size(content)
        file_sizes.append({
            "path": file_info["path"],
            "size": size,
            "content_lines": file_info["content_lines"]
        })
    
    file_sizes.sort(key=lambda x: x["size"], reverse=True)
    
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

def create_gist_content(gist_data, part_index, total_parts, parsed_data):
    """Crée le contenu d'un Gist"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    content = []
    content.append("=" * 80)
    content.append(f"PROJECT_SHARE - PARTIE {part_index}/{total_parts}")
    content.append(f"Projet: {parsed_data['header']['project']}")
    content.append(f"Date: {timestamp}")
    content.append(f"Fichiers: {len(gist_data['files'])}")
    content.append("=" * 80)
    content.append("")
    
    for file_info in gist_data["files"]:
        content.append("")
        content.append(f"FICHIER : {file_info['path']}")
        content.extend(file_info["content_lines"])
        content.append("")
    
    return '\n'.join(content)

def upload_gists_to_github(gist_parts, parsed_data, config, project_root):
    """Upload les Gists"""
    print("\n" + "="*60)
    print("UPLOAD VERS GITHUB GISTS")
    print("="*60)
    
    github_token = config.get("GITHUB_TOKEN")
    if not github_token:
        print("\n🔑 Token GitHub requis")
        github_token = input("Collez votre token GitHub: ").strip()
        if not github_token:
            print("✗ Token requis")
            return False
        config.save_token(github_token)
    
    headers = {"Authorization": f"token {github_token}"}
    
    try:
        test_response = requests.get("https://api.github.com/user", headers=headers)
        if test_response.status_code == 200:
            user = test_response.json().get('login')
            print(f"✓ Connecté: {user}")
        else:
            print(f"✗ Token invalide")
            return False
    except:
        print(f"✗ Erreur connexion")
        return False
    
    uploaded_gists = []
    print(f"\n🚀 Création de {len(gist_parts)} Gist(s)...")
    
    for i, gist_data in enumerate(gist_parts):
        part_index = i + 1
        total_parts = len(gist_parts)
        
        print(f"\n📤 Partie {part_index}/{total_parts} ({gist_data['size']/(1024*1024):.2f} MB)")
        
        content = create_gist_content(gist_data, part_index, total_parts, parsed_data)
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
                uploaded_gists.append({
                    "part": part_index,
                    "url": gist_response["html_url"],
                    "id": gist_response["id"]
                })
                print(f"  ✅ Créé")
            else:
                print(f"  ❌ Erreur {response.status_code}")
        except:
            print(f"  ❌ Exception")
    
    return uploaded_gists

def create_gist_index(uploaded_gists, config, project_root):
    """Crée l'index des Gists"""
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
        f.write("-"*80 + "\n\n")
        f.write("LIENS:\n")
        for gist in sorted(uploaded_gists, key=lambda x: x['part']):
            f.write(f"\nPartie {gist['part']:02d}: {gist['url']}")
        f.write("\n\n" + "="*80 + "\n")
    
    print(f"\n📄 Index créé: {index_file.name}")

def share_to_github_gists(config, project_root):
    """Partage sur GitHub Gists"""
    print("\n" + "="*60)
    print("SHARE TO GITHUB GISTS")
    print("="*60)
    
    project_share = project_root / "PROJECT_SHARE.txt"
    if not project_share.exists():
        print("✗ PROJECT_SHARE.txt introuvable!")
        print("   Générez-le d'abord avec l'option 1")
        return False
    
    parsed_data = parse_project_share_file(project_share)
    if not parsed_data:
        return False
    
    gist_parts = split_files_into_gists(parsed_data, config)
    if not gist_parts:
        return False
    
    uploaded = upload_gists_to_github(gist_parts, parsed_data, config, project_root)
    
    if uploaded:
        create_gist_index(uploaded, config, project_root)
        print("\n✅ OPÉRATION TERMINÉE")
        return True
    else:
        print("\n❌ Aucun Gist créé")
        return False


# ============================================================================
# AUTRES FONCTIONS
# ============================================================================

def create_diff_share(config, project_root):
    """Crée un rapport des différences Git"""
    print("\n" + "="*60)
    print("CREATE DIFF SHARE")
    print("="*60)
    
    try:
        result = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True, cwd=project_root)
        
        if not result.stdout.strip():
            print("ℹ Aucune différence")
            return True
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        diff_file = project_root / f"DIFF_REPORT_{timestamp}.txt"
        
        with open(diff_file, 'w', encoding='utf-8') as f:
            f.write(result.stdout)
        
        print(f"✅ Diff: {diff_file.name}")
    except:
        print("✗ Erreur Git")
        return False
    
    return True

def git_commit_push_publish(config, project_root):
    """Commit et push Git"""
    print("\n" + "="*60)
    print("GIT COMMIT + PUSH")
    print("="*60)
    
    try:
        subprocess.run(["git", "add", "."], cwd=project_root)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=project_root)
        
        if not status.stdout.strip():
            print("ℹ Aucun changement")
            return True
        
        default_msg = f"Mise à jour {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        commit_msg = input(f"Message (défaut: {default_msg}): ").strip() or default_msg
        
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=project_root)
        
        branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=project_root)
        current_branch = branch.stdout.strip() or "main"
        
        result = subprocess.run(["git", "push", "origin", current_branch], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print("✓ Push réussi")
            return True
        else:
            print("✗ Échec push")
            return False
    except:
        print("✗ Erreur Git")
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
        print(f"SHARE GITHUB V9.4 - {config.get('PROJECT_NAME')}")
        print("="*60)
        print(f"Projet: {project_root}")
        print(f"Config: {config.config_path}")
        print("\n" + "="*60)
        print("1. GÉNÉRER PROJECT_SHARE.txt")
        print("2. CREATE DIFF SHARE")
        print("3. GIT COMMIT + PUSH")
        print("4. SHARE TO GITHUB GISTS")
        print("5. EXIT")
        print("="*60)
        
        choice = input("\nChoix (1-5): ").strip()
        
        if choice == "1":
            create_full_share(config)
        elif choice == "2":
            create_diff_share(config, project_root)
        elif choice == "3":
            git_commit_push_publish(config, project_root)
        elif choice == "4":
            share_to_github_gists(config, project_root)
        elif choice == "5":
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