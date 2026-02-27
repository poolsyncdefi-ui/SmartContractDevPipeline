#!/usr/bin/env python3
"""
Share GitHub V8.1 - Version CORRIGÉE pour PROJECT_SHARE.txt
Traitement fiable du fichier de partage avec gestion d'erreurs améliorée
"""

import json
import os
import sys
import datetime
from pathlib import Path
import requests
import math

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Charge et gère la configuration depuis JSON"""
    
    def __init__(self, config_path="../project_config.json"):
        self.config_path = Path(config_path)
        self.default_config = {
            "PROJECT_NAME": "SmartContractDevPipeline",
            "GITHUB_USERNAME": "poolsyncdefi-ui",
            "GITHUB_TOKEN": "",
            "MAX_GIST_SIZE_MB": 45,  # Limite de sécurité (45 Mo au lieu de 50)
            "LINES_PER_GIST": 7000,   # Optionnel: pour un contrôle plus fin
        }
        self.config = self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        try:
            if self.config_path.exists():
                print(f"✓ Fichier config trouvé: {self.config_path}")
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Fusion avec valeurs par défaut
                for key, value in self.default_config.items():
                    if key not in config:
                        config[key] = value
                
                return config
        except Exception as e:
            print(f"⚠ Erreur chargement config: {e}")
        
        return self.default_config.copy()
    
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
# FONCTIONS PRINCIPALES POUR GISTS
# ============================================================================

def estimate_gist_size(content):
    """Estime la taille réelle d'un Gist en bytes (encodage UTF-8)"""
    return len(content.encode('utf-8'))

def split_project_share_file(input_file="PROJECT_SHARE.txt", config=None):
    """
    Lit PROJECT_SHARE.txt et le divise intelligemment en parties
    Respecte la structure des fichiers pour éviter les coupures au milieu
    """
    print("\n" + "="*60)
    print("ANALYSE ET DÉCOUPAGE DE PROJECT_SHARE.txt")
    print("="*60)
    
    if not os.path.exists(input_file):
        print(f"✗ Fichier introuvable: {input_file}")
        return None
    
    # Taille du fichier source
    file_size = os.path.getsize(input_file)
    file_size_mb = file_size / (1024 * 1024)
    print(f"📄 Fichier source: {input_file}")
    print(f"📊 Taille: {file_size:,} bytes ({file_size_mb:.2f} MB)")
    
    # Lire tout le fichier
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"✗ Erreur lecture: {e}")
        return None
    
    # Séparateur de fichiers dans PROJECT_SHARE.txt
    # Le format est: "FICHIER : chemin" puis le contenu, puis ligne vide
    lines = content.split('\n')
    total_lines = len(lines)
    print(f"📝 Lignes totales: {total_lines:,}")
    
    # Détecter les marqueurs de fichiers
    file_markers = []
    for i, line in enumerate(lines):
        if line.startswith("FICHIER : "):
            file_markers.append(i)
    
    print(f"📁 Fichiers détectés: {len(file_markers)}")
    
    if len(file_markers) == 0:
        print("⚠ Aucun marqueur 'FICHIER :' trouvé - format incorrect?")
        return None
    
    # Calculer la taille moyenne par fichier
    avg_lines_per_file = total_lines / len(file_markers)
    print(f"📊 Moyenne: {avg_lines_per_file:.0f} lignes par fichier")
    
    # Déterminer le nombre de Gists nécessaires
    # Option 1: Basé sur la taille (plus fiable)
    max_size_bytes = config.get("MAX_GIST_SIZE_MB", 45) * 1024 * 1024
    
    # Option 2: Basé sur les lignes (fallback)
    max_lines_per_gist = config.get("LINES_PER_GIST", 7000)
    
    # Calculer les deux méthodes et prendre la plus conservative
    estimated_gists_by_size = math.ceil(file_size / max_size_bytes)
    estimated_gists_by_lines = math.ceil(total_lines / max_lines_per_gist)
    num_gists = max(estimated_gists_by_size, estimated_gists_by_lines)
    
    print(f"\n📊 Découpage estimé:")
    print(f"  - Par taille ({max_size_bytes/(1024*1024):.0f} Mo): {estimated_gists_by_size} Gist(s)")
    print(f"  - Par lignes ({max_lines_per_gist} lignes): {estimated_gists_by_lines} Gist(s)")
    print(f"  - Total retenu: {num_gists} Gist(s)")
    
    # Découpage intelligent en respectant les frontières des fichiers
    gist_parts = []
    files_per_gist = math.ceil(len(file_markers) / num_gists)
    
    print(f"\n✂️ Découpage: ~{files_per_gist} fichiers par Gist")
    
    for gist_idx in range(num_gists):
        start_file_idx = gist_idx * files_per_gist
        end_file_idx = min((gist_idx + 1) * files_per_gist, len(file_markers))
        
        if start_file_idx >= len(file_markers):
            break
        
        # Déterminer les lignes de début et fin
        start_line = file_markers[start_file_idx]
        if end_file_idx < len(file_markers):
            end_line = file_markers[end_file_idx] - 1  # Jusqu'à la veille du prochain marker
        else:
            end_line = total_lines - 1  # Jusqu'à la fin
        
        # Extraire le contenu
        part_lines = lines[start_line:end_line + 1]
        part_content = '\n'.join(part_lines)
        
        # Vérifier la taille
        part_size = estimate_gist_size(part_content)
        part_size_mb = part_size / (1024 * 1024)
        
        # Ajouter un en-tête de partie
        header = f"{'='*80}\n"
        header += f"PARTIE {gist_idx + 1}/{num_gists} - {config.get('PROJECT_NAME')}\n"
        header += f"Fichiers: {end_file_idx - start_file_idx}\n"
        header += f"Lignes: {len(part_lines)}\n"
        header += f"{'='*80}\n\n"
        
        full_part_content = header + part_content
        
        gist_parts.append({
            "index": gist_idx + 1,
            "total": num_gists,
            "content": full_part_content,
            "size": estimate_gist_size(full_part_content),
            "size_mb": part_size_mb,
            "files": end_file_idx - start_file_idx,
            "lines": len(part_lines)
        })
        
        print(f"  Partie {gist_idx + 1}: {part_size_mb:.2f} MB, {end_file_idx - start_file_idx} fichiers")
    
    return gist_parts

def upload_gists_to_github(gist_parts, config):
    """Upload les parties vers GitHub Gists"""
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
    
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Vérifier le token
    try:
        test_response = requests.get("https://api.github.com/user", headers=headers)
        if test_response.status_code == 200:
            user = test_response.json().get('login')
            print(f"✓ Connecté en tant que: {user}")
        else:
            print(f"✗ Token invalide: {test_response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Erreur connexion: {e}")
        return False
    
    uploaded_gists = []
    
    print(f"\n🚀 Création de {len(gist_parts)} Gist(s)...")
    
    for part in gist_parts:
        print(f"\n📤 Partie {part['index']}/{part['total']} ({part['size_mb']:.2f} MB, {part['files']} fichiers)")
        
        # Créer le nom de fichier
        filename = f"PROJECT_PART{part['index']:02d}_of_{part['total']:02d}.txt"
        
        data = {
            "description": f"{config.get('PROJECT_NAME')} - Partie {part['index']}/{part['total']} - {datetime.datetime.now().strftime('%Y-%m-%d')}",
            "public": True,
            "files": {
                filename: {
                    "content": part['content']
                }
            }
        }
        
        try:
            response = requests.post(
                "https://api.github.com/gists",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 201:
                gist_data = response.json()
                gist_url = gist_data["html_url"]
                uploaded_gists.append({
                    "part": part['index'],
                    "url": gist_url,
                    "id": gist_data["id"]
                })
                print(f"  ✅ Créé: {gist_url}")
            else:
                print(f"  ❌ Erreur {response.status_code}")
                print(f"     {response.text[:200]}")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
    
    return uploaded_gists

def create_gist_index(uploaded_gists, config):
    """Crée un fichier index avec tous les liens"""
    if not uploaded_gists:
        return
    
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    index_file = "GISTS_INDEX.txt"
    
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write(f"INDEX DES GISTS - {config.get('PROJECT_NAME')}\n")
        f.write("="*80 + "\n")
        f.write(f"Date: {timestamp}\n")
        f.write(f"Total Gists: {len(uploaded_gists)}\n")
        f.write(f"Visibilité: Public\n")
        f.write("-"*80 + "\n\n")
        
        f.write("LIENS:\n")
        for gist in sorted(uploaded_gists, key=lambda x: x['part']):
            f.write(f"\nPartie {gist['part']:02d}: {gist['url']}")
        
        f.write("\n\n" + "="*80 + "\n")
    
    print(f"\n📄 Index créé: {index_file}")
    print("   Contient les liens vers tous les Gists")

def share_to_github_gists(config):
    """Fonction principale - Option 4 du menu"""
    print("\n" + "="*60)
    print("SHARE TO GITHUB GISTS - VERSION CORRIGÉE")
    print("="*60)
    
    # 1. Vérifier que PROJECT_SHARE.txt existe
    if not os.path.exists("PROJECT_SHARE.txt"):
        print("✗ PROJECT_SHARE.txt introuvable!")
        print("   Générez-le d'abord avec l'option 1")
        return False
    
    # 2. Découper le fichier
    gist_parts = split_project_share_file("PROJECT_SHARE.txt", config)
    if not gist_parts:
        return False
    
    # 3. Upload sur GitHub
    uploaded = upload_gists_to_github(gist_parts, config)
    
    # 4. Créer l'index
    if uploaded:
        create_gist_index(uploaded, config)
        print("\n" + "="*60)
        print("✅ OPÉRATION TERMINÉE AVEC SUCCÈS")
        print("="*60)
        return True
    else:
        print("\n❌ Aucun Gist n'a pu être créé")
        return False

# ============================================================================
# FONCTIONS EXISTANTES À CONSERVER
# ============================================================================

def create_full_share(config):
    """Crée PROJECT_SHARE.txt (identique à votre version)"""
    print("\n" + "="*60)
    print("CREATE FULL SHARE")
    print("="*60)
    print("Cette fonction doit être implémentée avec votre logique existante")
    print("ou utilisez simplement le PROJECT_SHARE.txt que vous avez déjà")
    return True

def create_diff_share(config):
    """Crée un rapport des différences Git"""
    print("\n" + "="*60)
    print("CREATE DIFF SHARE")
    print("="*60)
    print("Fonction à implémenter selon vos besoins")
    return True

def git_commit_push_publish(config):
    """
    Effectue un commit et un push automatiques vers le dépôt GitHub.
    Gère les cas de figure courants (pas de changement, première push, etc.).
    """
    print("\n" + "="*60)
    print("GIT COMMIT + PUSH")
    print("="*60)

    import subprocess
    import os

    # 1. Vérifier qu'on est bien dans un dépôt Git
    try:
        subprocess.run(["git", "status"], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError:
        print("✗ Répertoire courant n'est pas un dépôt Git.")
        return False
    except FileNotFoundError:
        print("✗ Git n'est pas installé ou pas dans le PATH.")
        return False

    # 2. Obtenir un message de commit
    default_msg = f"Mise à jour automatique {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    print(f"\nMessage de commit (par défaut : \"{default_msg}\") :")
    commit_msg = input("> ").strip()
    if not commit_msg:
        commit_msg = default_msg

    # 3. Ajouter tous les changements
    print("\n📦 Ajout des fichiers modifiés...")
    result_add = subprocess.run(["git", "add", "."], capture_output=True, text=True)
    if result_add.returncode != 0:
        print(f"✗ Erreur lors de git add : {result_add.stderr}")
        return False

    # 4. Vérifier s'il y a des changements à commiter
    result_status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not result_status.stdout.strip():
        print("ℹ Aucun changement à commiter.")
        return True  # Ce n'est pas une erreur, on sort proprement

    # 5. Commit
    print("📝 Création du commit...")
    result_commit = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
    if result_commit.returncode != 0:
        print(f"✗ Erreur lors du commit : {result_commit.stderr}")
        return False
    print(f"✓ Commit créé : {commit_msg}")

    # 6. Push vers GitHub
    print("☁ Push vers GitHub...")
    # Récupérer le nom de la branche courante
    branch_result = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
    current_branch = branch_result.stdout.strip()

    if not current_branch:
        # Fallback : si pas de branche (détaché HEAD), on utilise "main"
        current_branch = "main"

    # Tenter le push
    result_push = subprocess.run(["git", "push", "origin", current_branch], capture_output=True, text=True)

    if result_push.returncode == 0:
        print(f"✓ Push réussi vers origin/{current_branch}")
        print("="*60)
        return True
    else:
        # Analyser les erreurs courantes
        error_msg = result_push.stderr.lower()
        if "no upstream branch" in error_msg:
            print("ℹ Branche locale n'a pas de branche amont. Tentative de push avec -u...")
            result_push_u = subprocess.run(["git", "push", "-u", "origin", current_branch], capture_output=True, text=True)
            if result_push_u.returncode == 0:
                print(f"✓ Push réussi (upstream configuré) vers origin/{current_branch}")
                return True
            else:
                print(f"✗ Échec du push : {result_push_u.stderr}")
        else:
            print(f"✗ Erreur lors du push : {result_push.stderr}")
        return False

# ============================================================================
# MENU PRINCIPAL
# ============================================================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main_menu(config):
    while True:
        clear_screen()
        print("\n" + "="*60)
        print(f"SHARE GITHUB V8.1 - {config.get('PROJECT_NAME')}")
        print("="*60)
        
        token = config.get("GITHUB_TOKEN")
        token_status = "✓ Configuré" if token else "✗ Non configuré"
        print(f"GitHub Token: {token_status}")
        
        print("\n" + "="*60)
        print("MENU PRINCIPAL")
        print("="*60)
        print("1. CREATE FULL SHARE (génère PROJECT_SHARE.txt)")
        print("2. CREATE DIFF SHARE")
        print("3. GIT COMMIT + PUSH + PUBLISH")
        print("4. SHARE TO GITHUB GISTS (CORRIGÉ) ← NOUVEAU")
        print("5. CONFIGURATION")
        print("6. EXIT")
        print("="*60)
        
        choice = input("\nVotre choix (1-6): ").strip()
        
        if choice == "1":
            create_full_share(config)
        elif choice == "2":
            create_diff_share(config)
        elif choice == "3":
            git_commit_push_publish(config)
        elif choice == "4":
            share_to_github_gists(config)
        elif choice == "5":
            configuration_menu(config)
        elif choice == "6":
            print("\nAu revoir!")
            break
        
        input("\nAppuyez sur ENTER pour continuer...")

def configuration_menu(config):
    """Menu de configuration simplifié"""
    while True:
        clear_screen()
        print("\n" + "="*60)
        print("CONFIGURATION")
        print("="*60)
        
        print(f"1. PROJECT_NAME: {config.get('PROJECT_NAME')}")
        token = config.get("GITHUB_TOKEN")
        masked = token[:4] + "..." + token[-4:] if token and len(token) > 8 else "Non configuré"
        print(f"2. GITHUB_TOKEN: {masked}")
        print(f"3. MAX_GIST_SIZE_MB: {config.get('MAX_GIST_SIZE_MB')} Mo")
        print(f"4. LINES_PER_GIST: {config.get('LINES_PER_GIST')}")
        print("5. Retour")
        
        choice = input("\nVotre choix (1-5): ").strip()
        
        if choice == "1":
            new_name = input(f"Nouveau nom [{config.get('PROJECT_NAME')}]: ").strip()
            if new_name:
                config.config["PROJECT_NAME"] = new_name
        elif choice == "2":
            new_token = input("Nouveau token GitHub: ").strip()
            if new_token:
                config.config["GITHUB_TOKEN"] = new_token
        elif choice == "3":
            try:
                new_size = int(input(f"Nouvelle taille max (Mo) [{config.get('MAX_GIST_SIZE_MB')}]: "))
                config.config["MAX_GIST_SIZE_MB"] = new_size
            except:
                pass
        elif choice == "4":
            try:
                new_lines = int(input(f"Nouvelles lignes max [{config.get('LINES_PER_GIST')}]: "))
                config.config["LINES_PER_GIST"] = new_lines
            except:
                pass
        elif choice == "5":
            break

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("SHARE GITHUB V8.1 - Version CORRIGÉE")
    print("="*60)
    
    config = Config()
    
    try:
        main_menu(config)
    except KeyboardInterrupt:
        print("\n\nProgramme interrompu.")
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()