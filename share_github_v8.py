#!/usr/bin/env python3
"""
Share GitHub V8 - Python Version
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
import datetime

# ============================================================================
# CONFIGURATION - Version corrigée
# ============================================================================

class Config:
    """Charge et gère la configuration depuis JSON"""
    
    def __init__(self, config_path="../project_config.json"):
        self.config_path = Path(config_path)
        self.default_config = {
            "PROJECT_NAME": "SmartContractDevPipeline",
            "PROJECT_PATH": "D:\\Web3Projects\\SmartContractDevPipeline",
            "GITHUB_USERNAME": "poolsyncdefi-ui",
            "GITHUB_REPO_NAME": "SmartContractDevPipeline",
            "GITHUB_REPO_DESCRIPTION": "Pipeline de développement Smart Contracts",
            "GITHUB_REPO_PRIVATE": False,
            "GITHUB_TOKEN": "",
            "EXCLUDE_PATTERNS": [],
            "EXCLUDE_DIRS": [],
            "INCLUDE_PATTERNS": []
        }
        self.config = self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        try:
            if self.config_path.exists():
                print(f"✓ Fichier trouvé: {self.config_path.absolute()}")
                content = self.config_path.read_text(encoding='utf-8')
                print(f"✓ Taille: {len(content)} caractères")
                
                try:
                    config = json.loads(content)
                    print(f"✓ JSON parsé avec succès")
                    
                    # Vérifier le token
                    token = config.get('GITHUB_TOKEN')
                    if token:
                        print(f"✓ GITHUB_TOKEN: TROUVÉ ({len(token)} caractères)")
                        print(f"✓ Token: {token[:10]}...")
                    else:
                        print(f"✗ GITHUB_TOKEN: NON TROUVÉ")
                    
                    # Fusionner avec valeurs par défaut
                    for key, value in self.default_config.items():
                        if key not in config:
                            config[key] = value
                    
                    return config
                    
                except json.JSONDecodeError as e:
                    print(f"✗ Erreur JSON: {e}")
                    return self.default_config.copy()
                    
            else:
                print(f"✗ Fichier non trouvé: {self.config_path}")
                return self.default_config.copy()
                
        except Exception as e:
            print(f"✗ Erreur: {e}")
            return self.default_config.copy()
    
    def get(self, key, default=None):
        """Récupère une valeur de configuration"""
        if hasattr(self, 'config') and isinstance(self.config, dict):
            return self.config.get(key, default)
        return self.default_config.get(key, default)
    
    def save_token(self, token):
        """Sauvegarde le token dans la config"""
        self.config["GITHUB_TOKEN"] = token
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"✓ Token sauvegardé")
            return True
        except Exception as e:
            print(f"✗ Erreur sauvegarde: {e}")
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
    
    # Vérifier si le fichier est vide ou très petit
    try:
        if path.is_file():
            file_size = path.stat().st_size
            # Ignorer les fichiers vides ou très petits (moins de 100 bytes)
            if file_size < 100:
                return True
    except:
        pass  # Si on ne peut pas vérifier la taille, continuer
    
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
    """Crée un fichier de partage avec le MÊME FORMAT que les Gists"""
    print("\n" + "="*60)
    print("CREATE FULL SHARE (même format que Gists)")
    print("="*60)
    
    project_path = Path(config.get("PROJECT_PATH", "."))
    
    if not project_path.exists():
        print(f"✗ Chemin introuvable: {project_path}")
        return False
    
    print(f"Chemin du projet: {project_path}")
    print("Scanning des fichiers...")
    
    # Récupérer les fichiers (même logique que pour les Gists)
    all_files = []
    for item in project_path.rglob("*"):
        if item.is_file():
            if should_include(item, config) and not should_exclude(item, config):
                all_files.append(item)
    
    if len(all_files) == 0:
        print("✗ Aucun fichier à inclure!")
        return False
    
    print(f"✓ Fichiers à inclure: {len(all_files)}")
    
    with open("PROJECT_SHARE.txt", "w", encoding="utf-8") as f:
        # MÊME EN-TÊTE que les Gists
        f.write(f"PROJECT: {config.get('PROJECT_NAME')}\n")
        f.write(f"DATE: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"FILES: {len(all_files)}\n")
        f.write("="*80 + "\n\n")
        
        # MÊME FORMAT que les Gists : FICHIER : chemin_complet
        for file_idx, file_path in enumerate(all_files, 1):
            # CHEMIN COMPLET ABSOLU (comme dans les Gists)
            full_path = str(file_path.absolute())
            f.write(f"FICHIER : {full_path}\n")
            
            try:
                # CONTENU avec numéros de ligne (comme dans les Gists)
                with open(file_path, 'r', encoding='utf-8') as file_content:
                    lines = file_content.readlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        f.write(f"{line_num:4d}: {line.rstrip()}\n")
                
                # Même séparateur
                if file_idx < len(all_files):
                    f.write("\n")
                    
            except Exception as e:
                f.write(f"[ERROR READING FILE: {e}]\n")
                if file_idx < len(all_files):
                    f.write("\n")
    
    file_size = os.path.getsize("PROJECT_SHARE.txt")
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"\n✓ Fichier créé: PROJECT_SHARE.txt")
    print(f"✓ Taille: {file_size:,} bytes ({file_size_mb:.2f} MB)")
    print(f"✓ Fichiers inclus: {len(all_files)}")
    print("✓ Même format que les Gists GitHub")
    
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
        f.write("SmartContractDevPipeline - DIFF REPORT\n")
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
    """Partage sur GitHub Gists avec format ULTRA SIMPLE"""
    print("\n" + "="*60)
    print("SHARE TO GITHUB GISTS (ULTRA SIMPLE FORMAT)")
    print("="*60)
    
    github_token = config.get("GITHUB_TOKEN")
    
    if not github_token or github_token.strip() == "":
        print("\n🔑 TOKEN GITHUB REQUIS")
        github_token = input("Collez votre token GitHub (avec permission gist): ").strip()
        if github_token:
            config.save_token(github_token)
        else:
            print("✗ Aucun token fourni")
            return False
    
    print("\n📝 Création du contenu pour Gists...")
    
    project_path = Path(config.get("PROJECT_PATH", "."))
    
    if not project_path.exists():
        print(f"✗ Chemin introuvable: {project_path}")
        return False
    
    # Récupérer les fichiers à inclure
    all_files = []
    for item in project_path.rglob("*"):
        if item.is_file():
            if should_include(item, config) and not should_exclude(item, config):
                all_files.append(item)
    
    if len(all_files) == 0:
        print("✗ Aucun fichier à inclure!")
        return False
    
    print(f"✓ Fichiers à inclure: {len(all_files)}")
    
    # Créer le contenu DIRECTEMENT
    gist_content_parts = []
    
    # En-tête minimal
    gist_content_parts.append(f"PROJECT: {config.get('PROJECT_NAME')}\n")
    gist_content_parts.append(f"DATE: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    gist_content_parts.append(f"FILES: {len(all_files)}\n")
    gist_content_parts.append("="*80 + "\n\n")
    
    # Pour chaque fichier : CHEMIN COMPLET + CONTENU
    for file_idx, file_path in enumerate(all_files, 1):
        # CHEMIN COMPLET ABSOLU du fichier
        full_path = str(file_path.absolute())
        gist_content_parts.append(f"FICHIER : {full_path}\n")
        
        try:
            # CONTENU avec numéros de ligne
            with open(file_path, 'r', encoding='utf-8') as file_content:
                lines = file_content.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    gist_content_parts.append(f"{line_num:4d}: {line.rstrip()}\n")
            
            # Séparateur minimal entre fichiers
            if file_idx < len(all_files):
                gist_content_parts.append("\n")
                
        except Exception as e:
            gist_content_parts.append(f"[ERROR READING FILE: {e}]\n")
            if file_idx < len(all_files):
                gist_content_parts.append("\n")
    
    # Joindre tout le contenu
    gist_content = "".join(gist_content_parts)
    content_size = len(gist_content.encode('utf-8'))
    content_size_mb = content_size / (1024 * 1024)
    
    print(f"✓ Contenu créé: {content_size:,} bytes ({content_size_mb:.2f} MB)")
    print(f"📢 Gist sera PUBLIC")
    
    # CORRECTION : TOUJOURS PUBLIC
    is_public = True
    
    # Vérifier la taille
    if content_size_mb > 1:
        print(f"\n⚠ Le contenu dépasse la limite de 1 MB ({content_size_mb:.2f} MB > 1 MB)")
        print("➡ Division automatique en plusieurs Gists...")
        
        # Diviser le contenu
        return split_and_upload_from_content(config, github_token, gist_content, is_public)
    else:
        # Fichier < 1 MB - upload direct MAIS créer GISTS_INDEX.txt
        print(f"\n✓ Contenu < 1 MB ({content_size_mb:.2f} MB) - Upload direct")
        
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # CORRECTION : FORCER À True
        data = {
            "description": f"{config.get('PROJECT_NAME')} - Full Project {datetime.datetime.now().strftime('%Y-%m-%d')}",
            "public": True,  # CORRECTION ICI : True au lieu de is_public
            "files": {
                "PROJECT_SHARE.txt": {
                    "content": gist_content
                }
            }
        }
        
        print(f"\nEnvoi vers GitHub Gists...")
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
                print(f"Public: Oui")
                
                # CRÉER GISTS_INDEX.txt POUR UN SEUL GIST AUSSI
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                with open("GISTS_INDEX.txt", "w", encoding="utf-8") as f:
                    f.write("="*80 + "\n")
                    f.write(f"GITHUB GISTS INDEX - {config.get('PROJECT_NAME')}\n")
                    f.write("="*80 + "\n")
                    f.write("📋 CONTEXTE DE LA SESSION\n")
                    f.write(f"  Projet: {config.get('PROJECT_NAME')}\n")
                    f.write(f"  Date: {timestamp}\n")
                    f.write(f"  Dépôt: https://github.com/{config.get('GITHUB_USERNAME')}/{config.get('GITHUB_REPO_NAME')}\n")
                    f.write(f"  Gists créés: 1\n")
                    f.write(f"  Visibilité: Public\n")
                    f.write(f"  Script: share_github_v8.py\n")
                    f.write("="*80 + "\n\n")
                    
                    f.write("📝 INSTRUCTIONS\n")
                    f.write("-"*79 + "\n")
                    f.write("• Ce Gist contient le code source du projet\n")
                    f.write("• Chaque fichier montre son chemin COMPLET\n")
                    f.write("• Les fichiers incluent leurs numéros de ligne originaux\n")
                    f.write("• Le Gist est PUBLIC\n")
                    f.write("\n")
                    
                    f.write("🔗 GIST DE CETTE SESSION\n")
                    f.write("-"*79 + "\n\n")
                    f.write(f"Gist: {gist_url}\n")
                    
                    f.write("\n" + "="*80 + "\n")
                    f.write(f"📅 Session terminée: {timestamp}\n")
                    f.write("="*80 + "\n")
                
                print(f"\n✓ GISTS_INDEX.txt créé avec le Gist")
                return True
            else:
                print(f"✗ Erreur API GitHub: {response.status_code}")
                print(f"Message: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"✗ Erreur connexion: {e}")
            return False

def split_and_upload_from_content(config, github_token, content, is_public=True):
    """Divise le contenu et upload sur plusieurs Gists - Écrase l'index"""
    print("\n" + "="*60)
    print("SPLIT AND UPLOAD TO GISTS (NOUVELLE SESSION)")
    print("="*60)
    
    print(f"📊 Analyse du contenu...")
    print(f"  Taille: {len(content):,} caractères")
    
    # Diviser par lignes
    lines = content.split('\n')
    total_lines = len(lines)
    max_lines_per_gist = 8000  # Environ 400-500KB
    num_parts = (total_lines // max_lines_per_gist) + 1
    
    print(f"  Lignes totales: {total_lines:,}")
    print(f"  Lignes par Gist: {max_lines_per_gist:,}")
    print(f"  Nombre de parties estimé: {num_parts}")
    
    gist_urls = []
    gist_ids = []
    
    print(f"\n🚀 Publication des Gists...")
    
    for part_num in range(1, num_parts + 1):
        start_idx = (part_num - 1) * max_lines_per_gist
        end_idx = min(part_num * max_lines_per_gist, total_lines)
        
        print(f"\n  Partie {part_num}/{num_parts} (lignes {start_idx+1:,}-{end_idx:,})")
        
        # Extraire les lignes pour cette partie
        part_lines = lines[start_idx:end_idx]
        part_content = "\n".join(part_lines)
        
        # Vérifier si le contenu n'est pas vide
        if not part_content.strip():
            print(f"    ⚠ Vide, ignorée")
            continue
        
        # Préparer la requête API
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # CORRECTION : FORCER À True
        data = {
            "description": f"{config.get('PROJECT_NAME')} - Part {part_num}/{num_parts}",
            "public": True,  # CORRECTION ICI : True au lieu de is_public
            "files": {
                f"PROJECT_PART{part_num}.txt": {
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
                gist_id = gist_data["id"]
                gist_urls.append(gist_url)
                gist_ids.append(gist_id)
                print(f"    ✅ Créé: {gist_url}")
            else:
                print(f"    ❌ Erreur HTTP {response.status_code}")
                print(f"      Message: {response.text[:100]}...")
                
        except Exception as e:
            print(f"    ❌ Erreur: {e}")
    
    # CRÉATION/ÉCRASEMENT DE GISTS_INDEX.txt
    if gist_urls:
        print("\n" + "="*60)
        print("✅ SESSION TERMINÉE - MISE À JOUR INDEX")
        print("="*60)
        print(f"Gists créés dans cette session: {len(gist_urls)}")
        
        # ÉCRASER GISTS_INDEX.txt avec NOUVEAU contenu
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open("GISTS_INDEX.txt", "w", encoding="utf-8") as f:
            # ======== EN-TÊTE ========
            f.write("="*80 + "\n")
            f.write(f"GITHUB GISTS INDEX - {config.get('PROJECT_NAME')}\n")
            f.write("="*80 + "\n")
            f.write("📋 CONTEXTE DE LA SESSION\n")
            f.write(f"  Projet: {config.get('PROJECT_NAME')}\n")
            f.write(f"  Date: {timestamp}\n")
            f.write(f"  Dépôt: https://github.com/{config.get('GITHUB_USERNAME')}/{config.get('GITHUB_REPO_NAME')}\n")
            f.write(f"  Gists créés: {len(gist_urls)}\n")
            f.write(f"  Visibilité: Public")  # CORRECTION : Toujours Public
            f.write(f"  Script: share_github_v8.py\n")
            f.write("="*80 + "\n\n")
            
            # ======== INSTRUCTIONS ========
            f.write("📝 INSTRUCTIONS\n")
            f.write("-"*79 + "\n")
            f.write("• Ces Gists contiennent le code source du projet\n")
            f.write("• Chaque fichier montre son chemin COMPLET\n")
            f.write("• Les fichiers incluent leurs numéros de ligne originaux\n")
            f.write("• Tous les Gists sont PUBLICS\n")  # CORRECTION : Toujours Publics
            f.write("• Combinez toutes les parties pour reconstituer le projet\n")
            f.write("\n")
            
            # ======== LISTE DES GISTS ========
            f.write("🔗 GISTS DE CETTE SESSION\n")
            f.write("-"*79 + "\n\n")
            
            for i, url in enumerate(gist_urls, 1):
                f.write(f"Partie {i}: {url}\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write(f"📅 Session terminée: {timestamp}\n")
            f.write("="*80 + "\n")
        
        print(f"✓ GISTS_INDEX.txt ÉCRASÉ")
        print(f"  Contient {len(gist_urls)} Gists de cette session")
        
        return True
    
    print("\n❌ Aucun Gist créé")
    return False

def split_and_upload_gists(config, github_token, is_public=True):
    """Divise et upload sur plusieurs Gists - TOUJOURS PUBLIC"""
    print("\n" + "="*60)
    print("SPLIT AND UPLOAD TO MULTIPLE GISTS (PUBLIC)")
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
    print(f"Public: Oui")  # CORRECTION : Toujours Oui
    
    gist_urls = []
    
    for part_num in range(1, num_parts + 1):
        start_idx = (part_num - 1) * max_lines_per_gist
        end_idx = min(part_num * max_lines_per_gist, total_lines)
        
        print(f"\nPartie {part_num}/{num_parts} (lignes {start_idx+1}-{end_idx})")
        
        # Extraire les lignes pour cette partie
        part_lines = lines[start_idx:end_idx]
        part_content = "".join(part_lines)
        
        # Vérifier si le contenu n'est pas vide
        if not part_content.strip():
            print(f"⚠ Partie {part_num} vide, ignorée")
            continue
        
        # Préparer la requête API
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # CORRECTION : FORCER À True
        data = {
            "description": f"{config.get('PROJECT_NAME')} - Part {part_num}/{num_parts} {datetime.datetime.now().strftime('%Y-%m-%d')}",
            "public": True,  # CORRECTION ICI : True au lieu de is_public
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
                print(f"  Message: {response.text}")
                
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
            f.write(f"Public: Yes\n")  # CORRECTION : Toujours Yes
            f.write("\nGIST URLs:\n\n")
            
            for i, url in enumerate(gist_urls, 1):
                f.write(f"Part {i}: {url}\n")
        
        print("\n" + "="*60)
        print("✅ TOUS LES GISTS CRÉÉS !")
        print("="*60)
        print(f"Nombre de Gists: {len(gist_urls)}")
        print(f"Public: Oui")  # CORRECTION : Toujours Oui
        print(f"Index sauvegardé dans: GISTS_INDEX.txt")
        
        # Afficher les URLs
        print("\nURLs des Gists:")
        for i, url in enumerate(gist_urls, 1):
            print(f"  Part {i}: {url}")
        
        return True
    
    print("✗ Aucun Gist créé (contenu vide?)")
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