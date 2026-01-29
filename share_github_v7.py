#!/usr/bin/env python3
"""
Share GitHub V7 - Python Version
Lit la configuration depuis project_config.json
"""

import json
import os
import sys
import subprocess
import datetime
from pathlib import Path
import requests
import re
import fnmatch

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Charge et gère la configuration depuis JSON"""
    
    def __init__(self, config_path="../project_config.json"):
        self.config_path = Path(config_path)
        self.default_config = {
            "PROJECT_NAME": "Structured Lending Protocol",
            "PROJECT_PATH": ".",
            "GITHUB_USERNAME": "poolsyncdefi-ui",
            "GITHUB_REPO_NAME": "structured-lending-protocol-clean",
            "GITHUB_REPO_DESCRIPTION": "Structured Lending Protocol Clean Version",
            "GITHUB_REPO_PRIVATE": False,
            "GITHUB_TOKEN": "",
            "EXCLUDE_PATTERNS": [],
            "EXCLUDE_DIRS": [],
            "INCLUDE_PATTERNS": []
        }
        self.config = self.load_config()
        
    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✓ Configuration chargée depuis: {self.config_path}")
                return {**self.default_config, **config}  # Merge avec defaults
            except Exception as e:
                print(f"⚠ Erreur lecture config: {e}")
                return self.default_config
        else:
            print(f"⚠ Fichier config non trouvé: {self.config_path}")
            print("Utilisation des valeurs par défaut")
            return self.default_config
    
    def get(self, key, default=None):
        """Récupère une valeur de configuration"""
        return self.config.get(key, default)
    
    def save_token(self, token):
        """Sauvegarde le token dans la config"""
        self.config["GITHUB_TOKEN"] = token
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✓ Token sauvegardé dans: {self.config_path}")
            return True
        except Exception as e:
            print(f"✗ Erreur sauvegarde token: {e}")
            return False

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def run_command(cmd, cwd=None, capture_output=True):
    """Exécute une commande shell"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, cwd=cwd, 
                                  capture_output=True, text=True, encoding='utf-8')
            return result.returncode, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=True, cwd=cwd)
            return result.returncode, "", ""
    except Exception as e:
        return -1, "", str(e)

def get_git_info():
    """Récupère les informations Git"""
    info = {}
    
    # Branche actuelle
    code, stdout, _ = run_command("git branch --show-current")
    if code == 0:
        info['branch'] = stdout.strip()
    
    # Dernier commit
    code, stdout, _ = run_command("git rev-parse --short HEAD")
    if code == 0:
        info['commit'] = stdout.strip()
    
    # Message du dernier commit
    code, stdout, _ = run_command('git log --oneline -1 --pretty=format:"%s"')
    if code == 0:
        info['last_commit_msg'] = stdout.strip()
    
    return info

def should_exclude(path, config):
    """Vérifie si un chemin doit être exclu"""
    path_str = str(path).replace('\\', '/')  # Normaliser les séparateurs
    path_name = path.name
    
    # Vérifier d'abord les dossiers complets (EXCLUDE_DIRS)
    exclude_dirs = config.get("EXCLUDE_DIRS", [])
    path_parts = path_str.split('/')  # Utiliser '/' normalisé
    
    for dir_name in exclude_dirs:
        if dir_name in path_parts:
            return True
    
    # Vérifier les patterns avec wildcards (EXCLUDE_PATTERNS)
    exclude_patterns = config.get("EXCLUDE_PATTERNS", [])
    
    for pattern in exclude_patterns:
        # Gérer les patterns de dossier avec /*
        if pattern.endswith('/*'):
            dir_pattern = pattern[:-2]
            if dir_pattern in path_parts:
                return True
            continue  # Ne pas vérifier plus loin pour les patterns de dossier
        
        # Pour les fichiers, utiliser fnmatch directement
        if fnmatch.fnmatch(path_name, pattern) or fnmatch.fnmatch(path_str, pattern):
            return True
    
    return False

def should_include(path, config):
    """Vérifie si un chemin doit être inclus (prioritaire sur exclude)"""
    path_str = str(path).replace('\\', '/')  # Normaliser les séparateurs
    path_name = path.name
    
    include_patterns = config.get("INCLUDE_PATTERNS", [])
    
    # Si pas de patterns d'inclusion définis, tout est inclus
    if not include_patterns:
        return True
    
    # Vérifier chaque pattern d'inclusion
    for pattern in include_patterns:
        if fnmatch.fnmatch(path_name, pattern) or fnmatch.fnmatch(path_str, pattern):
            return True
    
    # Si aucun pattern ne correspond, le fichier n'est pas inclus
    return False

# ============================================================================
# FONCTIONS DE PARTAGE
# ============================================================================

def create_full_share(config):
    """Crée un fichier de partage complet avec numéros de ligne"""
    print("\n" + "="*60)
    print("CREATE FULL SHARE")
    print("="*60)
    
    project_path = Path(config.get("PROJECT_PATH", "."))
    
    if not project_path.exists():
        print(f"✗ Chemin introuvable: {project_path}")
        return False
    
    print(f"Chemin du projet: {project_path}")
    print(f"Patterns d'inclusion: {len(config.get('INCLUDE_PATTERNS', []))}")
    print(f"Dossiers exclus: {len(config.get('EXCLUDE_DIRS', []))}")
    print(f"Patterns exclus: {len(config.get('EXCLUDE_PATTERNS', []))}")
    
    # Scanner les fichiers
    print("\nScanning des fichiers...")
    all_files = []
    scanned = 0
    excluded = 0
    
    for item in project_path.rglob("*"):
        if item.is_file():
            scanned += 1
            
            # Vérifier d'abord si le fichier doit être inclus
            if not should_include(item, config):
                excluded += 1
                continue
            
            # Vérifier ensuite si le fichier doit être exclu
            if should_exclude(item, config):
                excluded += 1
                continue
            
            all_files.append(item)
    
    print(f"\nRésultats du scan:")
    print(f"  Fichiers scannés: {scanned}")
    print(f"  Fichiers exclus: {excluded}")
    print(f"  Fichiers inclus: {len(all_files)}")
    
    if len(all_files) == 0:
        print("\n⚠ Aucun fichier à inclure!")
        print("Vérifiez vos patterns d'inclusion/exclusion dans project_config.json")
        return False
    
    with open("PROJECT_SHARE.txt", "w", encoding="utf-8") as f:
        # En-tête
        f.write("="*80 + "\n")
        f.write(f"STRUCTURED LENDING PROTOCOL - FULL PROJECT SHARE\n")
        f.write("="*80 + "\n")
        f.write(f"GitHub: {config.get('GITHUB_USERNAME')}/{config.get('GITHUB_REPO_NAME')}\n")
        f.write(f"Repo URL: https://github.com/{config.get('GITHUB_USERNAME')}/{config.get('GITHUB_REPO_NAME')}\n")
        f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n")
        
        # Informations Git
        git_info = get_git_info()
        f.write("[GIT INFORMATION]\n")
        f.write("-"*79 + "\n")
        if git_info.get('branch'):
            f.write(f"Branch: {git_info['branch']}\n")
        if git_info.get('commit'):
            f.write(f"Commit: {git_info['commit']}\n")
        if git_info.get('last_commit_msg'):
            f.write(f"Last commit: {git_info['last_commit_msg']}\n")
        f.write("\n")
        
        # Parcourir les fichiers AVEC FILTRAGE
        file_counters = {
            'contracts': 0,
            'scripts': 0,
            'tests': 0,
            'other': 0
        }
        
        # Grouper les fichiers par type pour un affichage organisé
        solidity_files = [f for f in all_files if f.suffix == '.sol']
        script_files = [f for f in all_files if f.suffix in ['.js', '.py', '.sh', '.bat', '.ps1', '.ts']]
        test_files = [f for f in all_files if any(test_dir in str(f) for test_dir in ['test', 'tests', '__tests__'])]
        other_files = [f for f in all_files if f not in solidity_files + script_files + test_files]
        
        # Fichiers Solidity (contrats)
        if solidity_files:
            f.write("[CONTRACTS DIRECTORY - *.sol files]\n")
            f.write("="*80 + "\n")
            
            for sol_file in solidity_files:
                file_counters['contracts'] += 1
                relative_path = sol_file.relative_to(project_path)
                
                f.write(f"\nFILE {file_counters['contracts']} | {relative_path}\n")
                f.write(f"Size: {sol_file.stat().st_size} bytes | Modified: {datetime.datetime.fromtimestamp(sol_file.stat().st_mtime)}\n")
                f.write("-"*79 + "\n")
                
                try:
                    with open(sol_file, 'r', encoding='utf-8') as sf:
                        lines = sf.readlines()
                        for i, line in enumerate(lines, 1):
                            f.write(f"{i:5d}: {line.rstrip()}\n")
                except Exception as e:
                    f.write(f"[ERROR READING FILE: {e}]\n")
                
                f.write("-"*79 + "\n")
        
        # Fichiers de scripts
        if script_files:
            f.write(f"\n[SCRIPTS DIRECTORY]\n")
            f.write("="*80 + "\n")
            
            for script_file in script_files:
                file_counters['scripts'] += 1
                relative_path = script_file.relative_to(project_path)
                
                f.write(f"\nSCRIPT {file_counters['scripts']} | {relative_path}\n")
                f.write(f"Size: {script_file.stat().st_size} bytes | Type: {script_file.suffix} | ")
                f.write(f"Modified: {datetime.datetime.fromtimestamp(script_file.stat().st_mtime)}\n")
                f.write("-"*79 + "\n")
                
                try:
                    with open(script_file, 'r', encoding='utf-8') as sf:
                        lines = sf.readlines()
                        for i, line in enumerate(lines, 1):
                            f.write(f"{i:5d}: {line.rstrip()}\n")
                except Exception as e:
                    f.write(f"[ERROR READING FILE: {e}]\n")
                
                f.write("-"*79 + "\n")
        
        # Fichiers de test
        if test_files:
            f.write("\n[TESTS DIRECTORY]\n")
            f.write("="*80 + "\n")
            
            for test_file in test_files:
                file_counters['tests'] += 1
                relative_path = test_file.relative_to(project_path)
                
                f.write(f"\nTEST {file_counters['tests']} | {relative_path}\n")
                f.write(f"Size: {test_file.stat().st_size} bytes | Type: {test_file.suffix} | ")
                f.write(f"Modified: {datetime.datetime.fromtimestamp(test_file.stat().st_mtime)}\n")
                f.write("-"*79 + "\n")
                
                try:
                    with open(test_file, 'r', encoding='utf-8') as tf:
                        lines = tf.readlines()
                        for i, line in enumerate(lines, 1):
                            f.write(f"{i:5d}: {line.rstrip()}\n")
                except Exception as e:
                    f.write(f"[ERROR READING FILE: {e}]\n")
                
                f.write("-"*79 + "\n")
        
        # Autres fichiers (selon les patterns d'inclusion)
        if other_files:
            f.write("\n[OTHER FILES]\n")
            f.write("="*80 + "\n")
            
            for other_file in other_files:
                file_counters['other'] += 1
                relative_path = other_file.relative_to(project_path)
                
                f.write(f"\nFILE {file_counters['other']} | {relative_path}\n")
                f.write(f"Size: {other_file.stat().st_size} bytes | Type: {other_file.suffix} | ")
                f.write(f"Modified: {datetime.datetime.fromtimestamp(other_file.stat().st_mtime)}\n")
                f.write("-"*79 + "\n")
                
                try:
                    with open(other_file, 'r', encoding='utf-8') as of:
                        lines = of.readlines()
                        for i, line in enumerate(lines, 1):
                            f.write(f"{i:5d}: {line.rstrip()}\n")
                except Exception as e:
                    f.write(f"[ERROR READING FILE: {e}]\n")
                
                f.write("-"*79 + "\n")
        
        # Structure du projet (version filtrée)
        f.write("\n[PROJECT FILE STRUCTURE - FILTERED]\n")
        f.write("="*80 + "\n")
        f.write("Listing filtered project files...\n\n")
        
        for item in all_files:
            relative_path = item.relative_to(project_path)
            f.write(f"{relative_path}\n")
        
        # Résumé
        total_files = sum(file_counters.values())
        f.write("\n" + "="*80 + "\n")
        f.write("[SUMMARY]\n")
        f.write("="*80 + "\n")
        f.write(f"Total contract files: {file_counters['contracts']}\n")
        f.write(f"Total script files: {file_counters['scripts']}\n")
        f.write(f"Total test files: {file_counters['tests']}\n")
        f.write(f"Total other files: {file_counters['other']}\n")
        f.write(f"Total code files: {total_files}\n")
        f.write(f"\nGenerated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n")
    
    print(f"\n✓ Fichier créé: PROJECT_SHARE.txt")
    print(f"✓ Fichiers inclus: {total_files}")
    print(f"  - Contrats: {file_counters['contracts']}")
    print(f"  - Scripts: {file_counters['scripts']}")
    print(f"  - Tests: {file_counters['tests']}")
    print(f"  - Autres: {file_counters['other']}")
    return True

def create_diff_share():
    """Crée un rapport des changements"""
    print("\n" + "="*60)
    print("CREATE DIFF SHARE")
    print("="*60)
    
    # Vérifier si on est dans un repo Git
    code, stdout, stderr = run_command("git status")
    if code != 0:
        print("✗ Pas dans un repository Git ou Git non installé")
        return False
    
    with open("DIFF_REPORT.txt", "w", encoding="utf-8") as f:
        # En-tête
        f.write("="*80 + "\n")
        f.write("STRUCTURED LENDING PROTOCOL - DIFF REPORT\n")
        f.write("="*80 + "\n")
        f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("\n")
        
        # Status Git
        f.write("[GIT STATUS]\n")
        f.write("-"*79 + "\n")
        code, stdout, stderr = run_command("git status --porcelain")
        if code == 0 and stdout.strip():
            changed_files = stdout.strip().split('\n')
            f.write(f"Changed files: {len(changed_files)}\n\n")
            
            for file_status in changed_files:
                if file_status.strip():
                    status = file_status[:2].strip()
                    filename = file_status[3:].strip()
                    f.write(f"{status}: {filename}\n")
                    
                    # Afficher les différences
                    if status in ['M', 'A', '??']:
                        f.write("-"*40 + "\n")
                        if status == '??':  # Nouveau fichier
                            if os.path.exists(filename):
                                with open(filename, 'r', encoding='utf-8') as nf:
                                    lines = nf.readlines()
                                    for i, line in enumerate(lines, 1):
                                        f.write(f"{i:4d}: {line.rstrip()}\n")
                        else:  # Fichier modifié
                            code, diff_output, _ = run_command(f"git diff {filename}")
                            if code == 0 and diff_output:
                                f.write("Changes:\n")
                                f.write(diff_output)
                        f.write("-"*40 + "\n")
        else:
            f.write("No changes detected in the working directory.\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("[GIT DIFF SUMMARY]\n")
        f.write("-"*79 + "\n")
        code, stdout, stderr = run_command("git diff --stat")
        if code == 0 and stdout:
            f.write(stdout)
        else:
            f.write("No staged changes.\n")
    
    print("✓ Fichier créé: DIFF_REPORT.txt")
    return True

def git_commit_push_publish(config):
    """Commit, push et publication sur GitHub"""
    print("\n" + "="*60)
    print("GIT COMMIT + PUSH + PUBLISH TO GITHUB")
    print("="*60)
    
    github_token = config.get("GITHUB_TOKEN")
    username = config.get("GITHUB_USERNAME")
    repo_name = config.get("GITHUB_REPO_NAME")
    
    # Vérifier le token
    if not github_token or github_token.strip() == "":
        print("\n🔑 TOKEN GITHUB REQUIS")
        print("Pour créer un token:")
        print("1. https://github.com/settings/tokens")
        print("2. 'Generate new token (classic)'")
        print("3. Donnez un nom")
        print("4. Sélectionnez 'repo' (TOUTE la section)")
        print("5. 'Generate token'")
        print("6. Copiez le token (commence par 'ghp_')\n")
        
        github_token = input("Collez votre token GitHub: ").strip()
        if github_token:
            if config.save_token(github_token):
                print("✓ Token sauvegardé")
            else:
                print("⚠ Token non sauvegardé dans la config")
        else:
            print("✗ Aucun token fourni")
            return False
    
    # Demander le message de commit
    commit_msg = input("\nMessage de commit (ENTER pour défaut): ").strip()
    if not commit_msg:
        commit_msg = f"🚀 Automated commit: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Étape 1: Vérifier Git
    print("\n1. Vérification Git...")
    code, stdout, stderr = run_command("git --version")
    if code != 0:
        print("✗ Git non installé")
        print("Téléchargez depuis: https://git-scm.com/downloads")
        return False
    print("✓ Git installé")
    
    # Étape 2: Ajouter les fichiers
    print("2. Ajout des fichiers...")
    code, stdout, stderr = run_command("git add .")
    if code != 0:
        print(f"✗ Erreur git add: {stderr}")
        return False
    print("✓ Fichiers ajoutés")
    
    # Étape 3: Commit
    print("3. Commit...")
    code, stdout, stderr = run_command(f'git commit -m "{commit_msg}"')
    if code != 0:
        print(f"⚠ Erreur commit (peut être normal si pas de changements): {stderr}")
    
    # Étape 4: Configurer remote
    print("4. Configuration remote GitHub...")
    remote_url = f"https://x-access-token:{github_token}@github.com/{username}/{repo_name}.git"
    
    # Supprimer et recréer le remote
    run_command("git remote remove origin")
    code, stdout, stderr = run_command(f'git remote add origin "{remote_url}"')
    if code != 0:
        print(f"✗ Erreur configuration remote: {stderr}")
        return False
    print("✓ Remote configuré")
    
    # Étape 5: Push
    print("5. Push vers GitHub...")
    code, stdout, stderr = run_command("git branch -M main")
    code, stdout, stderr = run_command("git push -u origin main --force")
    
    if code == 0:
        print("\n" + "="*60)
        print("✅ PUBLICATION RÉUSSIE !")
        print("="*60)
        print(f"Repository: https://github.com/{username}/{repo_name}")
        print(f"Commit: {commit_msg}")
        
        # Afficher le dernier commit
        code, last_commit, _ = run_command('git log --oneline -1')
        if code == 0:
            print(f"Dernier commit: {last_commit.strip()}")
        
        return True
    else:
        print(f"\n✗ ERREUR PUSH: {stderr}")
        
        # Essayer méthode alternative
        print("\nEssai méthode alternative...")
        alt_remote_url = f"https://{username}:{github_token}@github.com/{username}/{repo_name}.git"
        run_command("git remote remove origin")
        run_command(f'git remote add origin "{alt_remote_url}"')
        
        code, stdout, stderr = run_command("git push -u origin main --force")
        if code == 0:
            print("✅ Publication réussie avec méthode alternative!")
            print(f"Repository: https://github.com/{username}/{repo_name}")
            return True
        else:
            print(f"✗ Échec méthode alternative: {stderr}")
            return False

def share_to_github_gists(config):
    """Partage sur GitHub Gists"""
    print("\n" + "="*60)
    print("SHARE TO GITHUB GISTS")
    print("="*60)
    
    github_token = config.get("GITHUB_TOKEN")
    
    # Vérifier le token
    if not github_token or github_token.strip() == "":
        print("\n🔑 TOKEN GITHUB REQUIS")
        print("Pour créer un token:")
        print("1. https://github.com/settings/tokens")
        print("2. 'Generate new token (classic)'")
        print("3. Donnez un nom")
        print("4. Sélectionnez 'gist' permission")
        print("5. 'Generate token'")
        print("6. Copiez le token (commence par 'ghp_')\n")
        
        github_token = input("Collez votre token GitHub (avec permission gist): ").strip()
        if github_token:
            if config.save_token(github_token):
                print("✓ Token sauvegardé")
            else:
                print("⚠ Token non sauvegardé dans la config")
        else:
            print("✗ Aucun token fourni")
            return False
    
    # Vérifier si le fichier de partage existe
    if not os.path.exists("PROJECT_SHARE.txt"):
        print("\n⚠ PROJECT_SHARE.txt non trouvé")
        create = input("Créer le fichier de partage d'abord? (o/n): ").lower()
        if create == 'o':
            create_full_share(config)
        else:
            print("✗ Opération annulée")
            return False
    
    # Vérifier la taille du fichier
    file_size = os.path.getsize("PROJECT_SHARE.txt")
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"\nFichier: PROJECT_SHARE.txt")
    print(f"Taille: {file_size} bytes ({file_size_mb:.2f} MB)")
    print(f"Limite Gist: 1 MB")
    
    if file_size_mb > 1:
        print("\n⚠ Le fichier dépasse la limite de 1 MB pour les Gists")
        print("Options:")
        print("1. Diviser en plusieurs Gists")
        print("2. Essayer quand même (peut échouer)")
        print("3. Annuler")
        
        choice = input("\nVotre choix (1-3): ").strip()
        if choice == '3':
            return False
        elif choice == '1':
            return split_and_upload_gists(config, github_token)
    
    # Lire le contenu du fichier
    try:
        with open("PROJECT_SHARE.txt", 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"✗ Erreur lecture fichier: {e}")
        return False
    
    # Préparer la requête API
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "description": f"{config.get('PROJECT_NAME')} - Full Project Share {datetime.datetime.now().strftime('%Y-%m-%d')}",
        "public": False,
        "files": {
            "PROJECT_SHARE.txt": {
                "content": content
            }
        }
    }
    
    print("\nEnvoi vers GitHub Gists...")
    try:
        response = requests.post("https://api.github.com/gists", 
                                headers=headers, 
                                json=data)
        
        if response.status_code == 201:
            gist_data = response.json()
            gist_url = gist_data["html_url"]
            gist_id = gist_data["id"]
            
            print("\n" + "="*60)
            print("✅ GIST CRÉÉ AVEC SUCCÈS !")
            print("="*60)
            print(f"URL: {gist_url}")
            print(f"ID: {gist_id}")
            
            # Sauvegarder l'info du Gist
            with open("GIST_INFO.txt", "w", encoding="utf-8") as f:
                f.write(f"Gist URL: {gist_url}\n")
                f.write(f"Gist ID: {gist_id}\n")
                f.write(f"Created: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Description: {data['description']}\n")
                f.write(f"File: PROJECT_SHARE.txt\n")
                f.write(f"Size: {file_size} bytes\n")
            
            print(f"\n✓ Informations sauvegardées dans: GIST_INFO.txt")
            return True
        else:
            print(f"✗ Erreur API GitHub: {response.status_code}")
            print(f"Message: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Erreur connexion: {e}")
        return False

def split_and_upload_gists(config, github_token):
    """Divise et upload sur plusieurs Gists"""
    print("\n" + "="*60)
    print("SPLIT AND UPLOAD TO MULTIPLE GISTS")
    print("="*60)
    
    # Lire le fichier
    try:
        with open("PROJECT_SHARE.txt", 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"✗ Erreur lecture fichier: {e}")
        return False
    
    total_lines = len(lines)
    max_lines_per_gist = 10000  # Environ 500KB-1MB selon la taille des lignes
    num_parts = (total_lines // max_lines_per_gist) + 1
    
    print(f"Lignes totales: {total_lines}")
    print(f"Lignes par Gist: {max_lines_per_gist}")
    print(f"Nombre de parties: {num_parts}")
    
    gist_urls = []
    
    for part_num in range(1, num_parts + 1):
        start_idx = (part_num - 1) * max_lines_per_gist
        end_idx = min(part_num * max_lines_per_gist, total_lines)
        
        print(f"\nPartie {part_num}/{num_parts} (lignes {start_idx+1}-{end_idx})")
        
        # Extraire les lignes pour cette partie
        part_lines = lines[start_idx:end_idx]
        part_content = "".join(part_lines)
        
        # Préparer la requête API
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "description": f"{config.get('PROJECT_NAME')} - Part {part_num}/{num_parts} {datetime.datetime.now().strftime('%Y-%m-%d')}",
            "public": False,
            "files": {
                f"PROJECT_SHARE_PART{part_num}.txt": {
                    "content": part_content
                }
            }
        }
        
        try:
            response = requests.post("https://api.github.com/gists", 
                                    headers=headers, 
                                    json=data)
            
            if response.status_code == 201:
                gist_data = response.json()
                gist_url = gist_data["html_url"]
                gist_urls.append(gist_url)
                print(f"✓ Partie {part_num} créée: {gist_url}")
            else:
                print(f"✗ Erreur partie {part_num}: {response.status_code}")
                
        except Exception as e:
            print(f"✗ Erreur partie {part_num}: {e}")
    
    # Créer un index des Gists
    if gist_urls:
        with open("GISTS_INDEX.txt", "w", encoding="utf-8") as f:
            f.write("="*60 + "\n")
            f.write("GITHUB GISTS INDEX\n")
            f.write("="*60 + "\n")
            f.write(f"Project: {config.get('PROJECT_NAME')}\n")
            f.write(f"Split into: {len(gist_urls)} parts\n")
            f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\nGIST URLs:\n\n")
            
            for i, url in enumerate(gist_urls, 1):
                f.write(f"Part {i}: {url}\n")
        
        print("\n" + "="*60)
        print("✅ TOUS LES GISTS CRÉÉS !")
        print("="*60)
        print(f"Nombre de Gists: {len(gist_urls)}")
        print(f"Index sauvegardé dans: GISTS_INDEX.txt")
        
        # Afficher les URLs
        print("\nURLs des Gists:")
        for i, url in enumerate(gist_urls, 1):
            print(f"  Part {i}: {url}")
        
        return True
    
    return False

# ============================================================================
# MENU PRINCIPAL
# ============================================================================

def clear_screen():
    """Efface l'écran"""
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu(config):
    """Affiche le menu principal"""
    while True:
        clear_screen()
        print("\n" + "="*60)
        print(f"SHARE GITHUB V7 - {config.get('PROJECT_NAME')}")
        print("="*60)
        print(f"Repo: {config.get('GITHUB_USERNAME')}/{config.get('GITHUB_REPO_NAME')}")
        print(f"Path: {config.get('PROJECT_PATH')}")
        
        # Afficher le statut du token
        token = config.get("GITHUB_TOKEN")
        if token and token.strip() != "":
            print(f"GitHub: CONFIGURÉ {'*' * min(len(token), 10)}...")
        else:
            print("GitHub: NON CONFIGURÉ")
        
        print("\n" + "="*60)
        print("MENU PRINCIPAL")
        print("="*60)
        print("1. CREATE FULL SHARE (all files with line numbers)")
        print("2. CREATE DIFF SHARE (changed files only)")
        print("3. GIT COMMIT + PUSH + PUBLISH TO GITHUB")
        print("4. SHARE TO GITHUB GISTS")
        print("5. CONFIGURATION")
        print("6. EXIT")
        print("="*60)
        
        choice = input("\nVotre choix (1-6): ").strip()
        
        if choice == "1":
            create_full_share(config)
            input("\nAppuyez sur ENTER pour continuer...")
        
        elif choice == "2":
            create_diff_share()
            input("\nAppuyez sur ENTER pour continuer...")
        
        elif choice == "3":
            git_commit_push_publish(config)
            input("\nAppuyez sur ENTER pour continuer...")
        
        elif choice == "4":
            share_to_github_gists(config)
            input("\nAppuyez sur ENTER pour continuer...")
        
        elif choice == "5":
            configuration_menu(config)
        
        elif choice == "6":
            print("\nAu revoir!")
            break
        
        else:
            print("Choix invalide!")
            input("\nAppuyez sur ENTER pour continuer...")

def configuration_menu(config):
    """Menu de configuration"""
    while True:
        clear_screen()
        print("\n" + "="*60)
        print("CONFIGURATION")
        print("="*60)
        
        print("\nConfiguration actuelle:")
        print(f"1. PROJECT_NAME: {config.get('PROJECT_NAME')}")
        print(f"2. PROJECT_PATH: {config.get('PROJECT_PATH')}")
        print(f"3. GITHUB_USERNAME: {config.get('GITHUB_USERNAME')}")
        print(f"4. GITHUB_REPO_NAME: {config.get('GITHUB_REPO_NAME')}")
        
        token = config.get("GITHUB_TOKEN")
        if token and token.strip() != "":
            masked_token = token[:4] + "*" * (len(token) - 8) + token[-4:] if len(token) > 8 else "***"
            print(f"5. GITHUB_TOKEN: {masked_token}")
        else:
            print("5. GITHUB_TOKEN: NON CONFIGURÉ")
        
        print(f"6. EXCLUDE_PATTERNS: {len(config.get('EXCLUDE_PATTERNS', []))} patterns")
        print(f"7. EXCLUDE_DIRS: {len(config.get('EXCLUDE_DIRS', []))} dossiers")
        print(f"8. INCLUDE_PATTERNS: {len(config.get('INCLUDE_PATTERNS', []))} patterns")
        
        print("\n9. Tester la connexion GitHub")
        print("10. Sauvegarder la configuration")
        print("11. Retour au menu principal")
        print("="*60)
        
        choice = input("\nVotre choix (1-11): ").strip()
        
        if choice == "1":
            new_name = input(f"Nouveau PROJECT_NAME [{config.get('PROJECT_NAME')}]: ").strip()
            if new_name:
                config.config["PROJECT_NAME"] = new_name
        
        elif choice == "2":
            new_path = input(f"Nouveau PROJECT_PATH [{config.get('PROJECT_PATH')}]: ").strip()
            if new_path:
                config.config["PROJECT_PATH"] = new_path
        
        elif choice == "3":
            new_user = input(f"Nouveau GITHUB_USERNAME [{config.get('GITHUB_USERNAME')}]: ").strip()
            if new_user:
                config.config["GITHUB_USERNAME"] = new_user
        
        elif choice == "4":
            new_repo = input(f"Nouveau GITHUB_REPO_NAME [{config.get('GITHUB_REPO_NAME')}]: ").strip()
            if new_repo:
                config.config["GITHUB_REPO_NAME"] = new_repo
        
        elif choice == "5":
            new_token = input("Nouveau GITHUB_TOKEN (ENTER pour effacer): ").strip()
            config.config["GITHUB_TOKEN"] = new_token
        
        elif choice == "6":
            print(f"\nEXCLUDE_PATTERNS actuel:")
            for i, pattern in enumerate(config.get('EXCLUDE_PATTERNS', [])[:10], 1):
                print(f"  {i}. {pattern}")
            if len(config.get('EXCLUDE_PATTERNS', [])) > 10:
                print(f"  ... et {len(config.get('EXCLUDE_PATTERNS', [])) - 10} autres")
            input("\nAppuyez sur ENTER pour continuer...")
        
        elif choice == "7":
            print(f"\nEXCLUDE_DIRS actuel:")
            for i, dir_name in enumerate(config.get('EXCLUDE_DIRS', [])[:10], 1):
                print(f"  {i}. {dir_name}")
            if len(config.get('EXCLUDE_DIRS', [])) > 10:
                print(f"  ... et {len(config.get('EXCLUDE_DIRS', [])) - 10} autres")
            input("\nAppuyez sur ENTER pour continuer...")
        
        elif choice == "8":
            print(f"\nINCLUDE_PATTERNS actuel:")
            for i, pattern in enumerate(config.get('INCLUDE_PATTERNS', [])[:10], 1):
                print(f"  {i}. {pattern}")
            if len(config.get('INCLUDE_PATTERNS', [])) > 10:
                print(f"  ... et {len(config.get('INCLUDE_PATTERNS', [])) - 10} autres")
            input("\nAppuyez sur ENTER pour continuer...")
        
        elif choice == "9":
            test_github_connection(config)
            input("\nAppuyez sur ENTER pour continuer...")
        
        elif choice == "10":
            try:
                with open(config.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config.config, f, indent=2, ensure_ascii=False)
                print("✓ Configuration sauvegardée!")
            except Exception as e:
                print(f"✗ Erreur sauvegarde: {e}")
            input("\nAppuyez sur ENTER pour continuer...")
        
        elif choice == "11":
            break

def test_github_connection(config):
    """Teste la connexion à l'API GitHub"""
    print("\n" + "="*60)
    print("TEST CONNEXION GITHUB")
    print("="*60)
    
    token = config.get("GITHUB_TOKEN")
    if not token or token.strip() == "":
        print("✗ Token GitHub non configuré")
        return
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get("https://api.github.com/user", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Connexion réussie!")
            print(f"   Utilisateur: {user_data.get('login')}")
            print(f"   Nom: {user_data.get('name', 'Non défini')}")
            print(f"   Email: {user_data.get('email', 'Non défini')}")
            
            # Tester les permissions
            print("\n🔍 Test des permissions...")
            
            # Tester permission gist
            try:
                gist_response = requests.post("https://api.github.com/gists", 
                                            headers=headers, 
                                            json={"description": "Test", "public": False, "files": {"test.txt": {"content": "test"}}})
                if gist_response.status_code in [201, 401, 403]:
                    print(f"   Permission gist: {'✅' if gist_response.status_code == 201 else '✗'}")
            except:
                print("   Permission gist: ✗")
                
        else:
            print(f"✗ Erreur connexion: {response.status_code}")
            print(f"   Message: {response.text}")
            
    except Exception as e:
        print(f"✗ Erreur réseau: {e}")

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SHARE GITHUB V7 - Python Version")
    print("="*60)
    
    # Charger la configuration
    config = Config()
    
    try:
        main_menu(config)
    except KeyboardInterrupt:
        print("\n\nProgramme interrompu. Au revoir!")
    except Exception as e:
        print(f"\n✗ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        input("\nAppuyez sur ENTER pour quitter...")