#!/usr/bin/env python3
"""
Share GitHub V9.16 - Version avec gestion améliorée de Git
"""

import json
import os
import sys
import datetime
import fnmatch
import subprocess
from pathlib import Path
import requests

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    def __init__(self):
        current_dir = Path.cwd()
        
        if current_dir.name == "SmartContractDevPipeline":
            self.project_root = current_dir
            self.parent_dir = current_dir.parent
        else:
            self.project_root = current_dir / "SmartContractDevPipeline"
            self.parent_dir = current_dir
        
        self.config_path = self.parent_dir / "project_config.json"
        self.config = self.load_config()
    
    def load_config(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "PROJECT_NAME": "SmartContractDevPipeline",
            "GITHUB_TOKEN": "",
            "GITHUB_USERNAME": "poolsyncdefi-ui",
            "GITHUB_REPO_NAME": "SmartContractDevPipeline",
            "PROJECT_PATH": str(self.project_root),
            "MAX_GIST_SIZE_MB": 45,
            "MAX_FILES_PER_GIST": 100,
            "MAX_FILE_SIZE_MB": 8,
            "EXCLUDE_PATTERNS": [],
            "EXCLUDE_DIRS": [],
            "INCLUDE_PATTERNS": ["*"]
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
    path_str = str(path)
    path_parts = path.parts
    
    exclude_dirs = config.get("EXCLUDE_DIRS", [])
    for part in path_parts:
        if part in exclude_dirs:
            return True
    
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
    if path.is_dir():
        return False
    
    include_patterns = config.get("INCLUDE_PATTERNS", ["*"])
    for pattern in include_patterns:
        if fnmatch.fnmatch(path.name, pattern):
            return True
    
    return False

def collect_files(project_path, config):
    all_files = []
    project_root = Path(project_path)
    
    if not project_root.exists():
        return []
    
    for root, dirs, files in os.walk(project_root):
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
    print("\n" + "="*50)
    print("📄 GÉNÉRATION PROJECT_SHARE.txt")
    
    project_path = config.get("PROJECT_PATH")
    if not project_path:
        print("✗ PROJECT_PATH non défini")
        return False
    
    project_root = Path(project_path)
    if not project_root.exists():
        print(f"✗ Chemin introuvable")
        return False
    
    files = collect_files(project_path, config)
    
    if not files:
        print("✗ Aucun fichier")
        return False
    
    output_file = project_root / "PROJECT_SHARE.txt"
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        out_f.write(f"PROJECT: {config.get('PROJECT_NAME')}\n")
        out_f.write(f"DATE: {timestamp}\n")
        out_f.write(f"FILES: {len(files)}\n")
        out_f.write("=" * 80 + "\n\n")
        
        for file_path in files:
            out_f.write(f"FICHIER : {file_path}\n")
            
            numbered_lines = read_file_with_line_numbers(file_path)
            for line in numbered_lines:
                out_f.write(line + '\n')
            
            out_f.write('\n')
    
    if output_file.exists():
        file_size = output_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        print(f"✅ {len(files)} fichiers - {file_size_mb:.2f} MB")
        return True
    else:
        print("❌ Échec")
        return False


# ============================================================================
# PRÉPARATION DES FICHIERS POUR GISTS
# ============================================================================

def split_large_file(content, filename, max_size_bytes):
    """Fractionne un fichier en parties de taille max_size_bytes"""
    lines = content.split('\n')
    total_size = len(content.encode('utf-8'))
    
    if total_size <= max_size_bytes:
        return [(filename, content)]
    
    nb_parts = (total_size + max_size_bytes - 1) // max_size_bytes
    size_per_part = total_size / nb_parts
    
    parts = []
    current_part = []
    current_size = 0
    part_num = 1
    
    for line in lines:
        line_size = len(line.encode('utf-8')) + 1
        if current_size + line_size > size_per_part * 1.2 and current_part:
            part_content = '\n'.join(current_part)
            base, ext = os.path.splitext(filename)
            part_filename = f"{base}_part{part_num:02d}{ext}"
            parts.append((part_filename, part_content))
            
            current_part = [line]
            current_size = line_size
            part_num += 1
        else:
            current_part.append(line)
            current_size += line_size
    
    if current_part:
        part_content = '\n'.join(current_part)
        base, ext = os.path.splitext(filename)
        part_filename = f"{base}_part{part_num:02d}{ext}"
        parts.append((part_filename, part_content))
    
    return parts

def estimate_content_size(content):
    return len(content.encode('utf-8'))

def prepare_files_for_gists(project_root, config):
    """Prépare les fichiers pour les Gists"""
    all_files = collect_files(project_root, config)
    all_files = [f for f in all_files if f.name not in ["PROJECT_SHARE.txt", "GISTS_INDEX.txt"]]
    
    max_file_size = config.get("MAX_FILE_SIZE_MB", 8) * 1024 * 1024
    
    prepared = []
    total_split = 0
    
    for file_path in all_files:
        numbered_lines = read_file_with_line_numbers(file_path)
        content = '\n'.join(numbered_lines)
        file_size = estimate_content_size(content)
        
        if file_size > max_file_size:
            parts = split_large_file(content, file_path.name, max_file_size)
            total_split += 1
            for part_filename, part_content in parts:
                prepared.append({
                    "path": str(file_path),
                    "name": part_filename,
                    "content": part_content,
                    "size": estimate_content_size(part_content),
                    "original": file_path.name
                })
        else:
            prepared.append({
                "path": str(file_path),
                "name": file_path.name,
                "content": content,
                "size": file_size,
                "original": None
            })
    
    prepared.sort(key=lambda x: x["size"], reverse=True)
    return prepared, total_split

def pack_gists(files, config):
    """Packaging optimisé des fichiers dans les Gists"""
    max_size = config.get("MAX_GIST_SIZE_MB", 45) * 1024 * 1024
    max_files = config.get("MAX_FILES_PER_GIST", 100)
    
    gists = []
    
    large = [f for f in files if f["size"] > 1024 * 1024]
    medium = [f for f in files if 100 * 1024 < f["size"] <= 1024 * 1024]
    small = [f for f in files if f["size"] <= 100 * 1024]
    
    for file in large + medium:
        best_gist = None
        best_fill = -1
        
        for gist in gists:
            if (gist["size"] + file["size"] <= max_size and 
                len(gist["files"]) < max_files):
                fill = gist["size"] / max_size
                if fill > best_fill:
                    best_fill = fill
                    best_gist = gist
        
        if best_gist:
            best_gist["files"].append(file)
            best_gist["size"] += file["size"]
        else:
            gists.append({
                "files": [file],
                "size": file["size"]
            })
    
    for file in small:
        candidates = []
        for gist in gists:
            if (gist["size"] + file["size"] <= max_size and 
                len(gist["files"]) < max_files):
                free_space = max_size - gist["size"]
                candidates.append((free_space, gist))
        
        if candidates:
            candidates.sort()
            gist = candidates[0][1]
            gist["files"].append(file)
            gist["size"] += file["size"]
        else:
            gists.append({
                "files": [file],
                "size": file["size"]
            })
    
    return gists


# ============================================================================
# UPLOAD GISTS
# ============================================================================

def create_gist_files(gist_data, part_idx, total_parts, project_name):
    """Crée le dictionnaire des fichiers pour un Gist"""
    files_dict = {}
    
    readme = f"""# {project_name} - Partie {part_idx}/{total_parts}
📊 {len(gist_data['files'])} fichiers - {gist_data['size']/(1024*1024):.2f} MB

📁 Fichiers:
"""
    for f in gist_data["files"]:
        if f["original"]:
            readme += f"  • {f['name']} (partie de {f['original']})\n"
        else:
            readme += f"  • {f['name']}\n"
    
    files_dict["README.txt"] = {"content": readme}
    
    for f in gist_data["files"]:
        files_dict[f["name"]] = {"content": f["content"]}
    
    return files_dict

def upload_to_github(gists, config, project_root):
    """Upload les Gists vers GitHub"""
    print("\n" + "="*50)
    print("📤 UPLOAD GISTS")
    
    valid_gists = [g for g in gists if g["files"]]
    
    if not valid_gists:
        print("✗ Aucun Gist à uploader")
        return None
    
    github_token = config.get("GITHUB_TOKEN")
    
    if not github_token:
        print("✗ Token GitHub manquant")
        github_token = input("🔑 Entrez votre token GitHub: ").strip()
        if github_token:
            config.save_token(github_token)
        else:
            return None
    
    headers = {"Authorization": f"token {github_token}"}
    
    try:
        print("🔄 Vérification du token...")
        test = requests.get("https://api.github.com/user", headers=headers)
        
        if test.status_code == 200:
            user = test.json()
            print(f"✓ Connecté: {user.get('login')}")
        else:
            print(f"✗ Erreur token: {test.status_code}")
            return None
    except Exception as e:
        print(f"✗ Erreur connexion: {e}")
        return None
    
    uploaded = []
    
    for idx, gist in enumerate(valid_gists, 1):
        size_mb = gist["size"] / (1024 * 1024)
        fill_pct = (gist["size"] / (config.get("MAX_GIST_SIZE_MB", 45) * 1024 * 1024)) * 100
        
        print(f"\n  [{idx}/{len(valid_gists)}] ", end="")
        print(f"{len(gist['files']):3d} fichiers - {size_mb:5.2f} MB ({fill_pct:3.0f}%)")
        
        files_dict = create_gist_files(gist, idx, len(valid_gists), config.get('PROJECT_NAME'))
        
        data = {
            "description": f"{config.get('PROJECT_NAME')} - Partie {idx}/{len(valid_gists)}",
            "public": True,
            "files": files_dict
        }
        
        try:
            print("    ⏳ Upload...", end="", flush=True)
            resp = requests.post("https://api.github.com/gists", headers=headers, json=data, timeout=300)
            
            if resp.status_code == 201:
                url = resp.json()["html_url"]
                print(f"\r    ✅ {url}")
                uploaded.append({
                    "part": idx,
                    "url": url,
                    "size": size_mb,
                    "files": len(gist["files"])
                })
            elif resp.status_code == 422:
                pass
            else:
                print(f"\r    ❌ Erreur {resp.status_code}")
        except Exception as e:
            if "422" not in str(e):
                print(f"\r    ❌ Exception: {e}")
    
    return uploaded

def save_index(uploaded, config, project_root):
    if not uploaded:
        return
    
    index_file = project_root / "GISTS_INDEX.txt"
    total_size = sum(g["size"] for g in uploaded)
    total_files = sum(g["files"] for g in uploaded)
    
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(f"{config.get('PROJECT_NAME')}\n")
        f.write(f"Date: {datetime.datetime.now()}\n")
        f.write(f"Gists: {len(uploaded)} | Fichiers: {total_files} | Taille: {total_size:.2f} MB\n\n")
        
        for g in sorted(uploaded, key=lambda x: x['part']):
            f.write(f"Partie {g['part']:02d}: {g['url']} ({g['files']} fichiers, {g['size']:.2f} MB)\n")
    
    print(f"\n📄 Index: {index_file.name}")

def share_to_gists(config, project_root):
    print("\n" + "="*50)
    print("📊 SHARE TO GISTS")
    
    files, nb_split = prepare_files_for_gists(project_root, config)
    gists = pack_gists(files, config)
    valid_gists = [g for g in gists if g["files"]]
    
    total_files = len(files)
    total_size = sum(f["size"] for f in files) / (1024 * 1024)
    
    print(f"\n📊 {total_files} fichiers ({total_size:.2f} MB) → {len(valid_gists)} Gists")
    if nb_split:
        print(f"   ({nb_split} fichiers fractionnés)")
    
    for i, g in enumerate(valid_gists, 1):
        fill = (g["size"] / (config.get("MAX_GIST_SIZE_MB", 45) * 1024 * 1024)) * 100
        print(f"   G{i:02d}: {len(g['files']):3d} fichiers, {g['size']/(1024*1024):5.2f} MB ({fill:3.0f}%)")
    
    uploaded = upload_to_github(gists, config, project_root)
    
    if uploaded:
        save_index(uploaded, config, project_root)
        print("\n✅ Terminé")
        return True
    
    return False


# ============================================================================
# GIT COMMIT + PUSH (VERSION CORRIGÉE)
# ============================================================================

def git_commit_push(config, project_root):
    print("\n" + "="*50)
    print("📦 GIT COMMIT + PUSH")
    
    try:
        # Vérifier si on est dans un repo git
        git_check = subprocess.run(["git", "rev-parse", "--git-dir"], 
                                   capture_output=True, text=True, cwd=project_root)
        if git_check.returncode != 0:
            print("✗ Pas un dépôt Git")
            return False
        
        # Vérifier les changements
        status = subprocess.run(["git", "status", "--porcelain"], 
                               capture_output=True, text=True, cwd=project_root)
        
        if not status.stdout.strip():
            print("ℹ Aucun changement à commiter")
            return True
        
        files = len(status.stdout.strip().split('\n'))
        print(f"📝 {files} fichier(s) modifié(s)")
        
        # Aperçu des fichiers modifiés
        print("\n📋 Fichiers modifiés:")
        for line in status.stdout.strip().split('\n')[:5]:  # Max 5 lignes
            print(f"   {line}")
        if len(status.stdout.strip().split('\n')) > 5:
            print("   ...")
        
        # Message de commit
        msg = input("\n💬 Message de commit (défaut): ").strip()
        if not msg:
            msg = f"Mise à jour {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Git add
        print("\n📥 Git add...")
        subprocess.run(["git", "add", "."], cwd=project_root, check=True)
        
        # Git commit
        print("📝 Git commit...")
        commit = subprocess.run(["git", "commit", "-m", msg], 
                               capture_output=True, text=True, cwd=project_root)
        if commit.returncode != 0:
            print(f"✗ Erreur commit: {commit.stderr}")
            return False
        print(f"✓ Commit créé: {commit.stdout}")
        
        # Récupérer la branche courante
        branch = subprocess.run(["git", "branch", "--show-current"], 
                               capture_output=True, text=True, cwd=project_root)
        current_branch = branch.stdout.strip() or "main"
        
        # Récupérer le remote
        remote = subprocess.run(["git", "remote"], 
                               capture_output=True, text=True, cwd=project_root)
        remotes = remote.stdout.strip().split('\n')
        
        if not remotes or not remotes[0]:
            print("✗ Aucun remote configuré")
            return False
        
        default_remote = remotes[0]
        print(f"\n🌐 Remote: {default_remote}, Branche: {current_branch}")
        
        # Vérifier l'authentification
        print("🔄 Vérification de l'authentification...")
        
        # Essayer de récupérer d'abord (pull) pour éviter les conflits
        print("📥 Git pull...")
        pull = subprocess.run(["git", "pull", default_remote, current_branch],
                             capture_output=True, text=True, cwd=project_root)
        if pull.returncode != 0:
            print(f"⚠ Warning pull: {pull.stderr}")
        
        # Git push
        print("📤 Git push...")
        push = subprocess.run(["git", "push", default_remote, current_branch],
                             capture_output=True, text=True, cwd=project_root)
        
        if push.returncode == 0:
            print("✓ Push réussi!")
            return True
        else:
            print(f"✗ Échec push:")
            error_msg = push.stderr.lower()
            
            if "authentication failed" in error_msg or "401" in error_msg:
                print("   Problème d'authentification - Vérifiez vos identifiants GitHub")
                print("   Suggestions:")
                print("   • git config --global user.name \"votre_nom\"")
                print("   • git config --global user.email \"votre_email\"")
                print("   • Utiliser un token personnel au lieu du mot de passe")
            elif "protected branch" in error_msg:
                print("   Branche protégée - Vous devez faire une pull request")
            elif "non-fast-forward" in error_msg:
                print("   Des changements distants existent - Faites git pull d'abord")
                print("   → git pull --rebase")
            else:
                print(f"   {push.stderr}")
            
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"✗ Erreur Git: {e}")
        return False
    except Exception as e:
        print(f"✗ Erreur inattendue: {e}")
        return False


# ============================================================================
# MENU PRINCIPAL
# ============================================================================

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    config = Config()
    
    while True:
        clear()
        print("\n" + "="*50)
        print(f"🚀 SHARE GITHUB V9.16 - {config.get('PROJECT_NAME')}")
        print("="*50)
        print("1. 📄 Générer PROJECT_SHARE.txt")
        print("2. 📦 Git commit + push")
        print("3. 📤 Partager vers Gists")
        print("4. ❌ Quitter")
        print("-"*50)
        
        choice = input("Choix: ").strip()
        
        if choice == "1":
            create_full_share(config)
        elif choice == "2":
            git_commit_push(config, config.project_root)
        elif choice == "3":
            share_to_gists(config, config.project_root)
        elif choice == "4":
            print("\n👋 Au revoir!")
            break
        
        input("\nAppuyez sur ENTER...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrompu")
    except Exception as e:
        print(f"\n✗ Erreur: {e}")