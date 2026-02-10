# find_string_error.py
import re

def find_unterminated_strings(filepath):
    """Trouve les chaînes non terminées dans un fichier Python"""
    print(f"🔍 Recherche d'erreurs dans: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Chercher les docstrings non fermées
    lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        # Compter les guillemets
        triple_double = line.count('"""')
        triple_single = line.count("'''")
        
        # Si nombre impair de guillemets triples
        if triple_double % 2 != 0 or triple_single % 2 != 0:
            print(f"⚠️  Ligne {i}: Chaîne triple potentiellement non fermée")
            print(f"   Contenu: {line[:100]}...")
        
        # Chercher les guillemets simples/doubles non fermés
        single_quotes = re.findall(r"(?<!\')'(?!\')", line)
        double_quotes = re.findall(r'(?<!")\"(?!")', line)
        
        if len(single_quotes) % 2 != 0:
            print(f"⚠️  Ligne {i}: Guillemet simple non fermé")
            print(f"   Contenu: {line[:100]}...")
        
        if len(double_quotes) % 2 != 0:
            print(f"⚠️  Ligne {i}: Guillemet double non fermé")
            print(f"   Contenu: {line[:100]}...")
    
    # Vérifier autour de la ligne 1940 spécifiquement
    print(f"\n🔍 Vérification détaillée autour de la ligne 1940:")
    start = max(1930, 0)
    end = min(1950, len(lines))
    
    for i in range(start, end):
        print(f"{i:4}: {lines[i]}")
    
    print("\n💡 CONSEIL: Vérifiez les docstrings autour de cette ligne")

if __name__ == "__main__":
    find_unterminated_strings("agents/coder/coder.py")