# SmartContractDevPipeline

Pipeline de développement automatisé pour smart contracts avec agents IA.

## 📁 Structure du projet

```
SmartContractDevPipeline/
├── agents/                    # Agents principaux
│   ├── architect/            # Agent architecte
│   │   ├── sous_agents/      # Sous-agents spécialisés
│   │   │   ├── cloud_architect/
│   │   │   ├── blockchain_architect/
│   │   │   └── microservices_architect/
│   │   ├── agent.py         # Agent principal
│   │   └── config.yaml      # Configuration
│   ├── coder/               # Agent développeur
│   ├── smart_contract/      # Agent smart contract
│   ├── frontend_web3/       # Agent frontend Web3
│   └── tester/              # Agent testeur
├── orchestrator/            # Orchestrateur principal
│   ├── orchestrator.py      # Code de l'orchestrateur
│   └── config.yaml         # Configuration globale
├── base_agent.py           # Classe de base pour tous les agents
├── requirements.txt        # Dépendances Python
├── docker-compose.yml      # Déploiement Docker
└── README.md              # Ce fichier
```

## 🚀 Démarrage rapide

### 1. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 2. Déploiement des agents

```bash
python deploy_pipeline.py
```

Options disponibles:
- `--path /chemin/vers/projet` : Chemin personnalisé du projet
- `--force` : Forcer le redéploiement complet
- `--verbose` : Mode détaillé

### 3. Tester l'orchestrateur

```bash
cd orchestrator
python orchestrator.py --test
```

### 4. Exécuter un workflow

```bash
python orchestrator.py --workflow full_pipeline
```

## 🔧 Agents et sous-agents

### Architecte (3 sous-agents)
- Cloud Architect
- Blockchain Architect
- Microservices Architect

### Développeur (3 sous-agents)
- Backend Developer
- Frontend Developer
- DevOps Engineer

### Smart Contract (4 sous-agents)
- Solidity Expert
- Security Expert
- Gas Optimizer
- Formal Verification

### Frontend Web3 (3 sous-agents)
- React/Next.js Expert
- Web3 Integration
- UI/UX Designer

### Testeur (4 sous-agents)
- Unit Tester
- Integration Tester
- E2E Tester
- Fuzzing Expert

## 🐛 Dépannage

### Problèmes d'import
```bash
export PYTHONPATH="$PYTHONPATH:D:\Web3Projects\SmartContractDevPipeline"
```

Ou exécuter depuis la racine du projet:
```bash
cd D:\Web3Projects\SmartContractDevPipeline
python deploy_pipeline.py
```

## 📝 Personnalisation

1. Modifier les configurations dans `agents/*/config.yaml`
2. Ajouter de nouveaux sous-agents dans `deploy_pipeline.py`
3. Créer de nouveaux workflows dans `orchestrator/config.yaml`

## 📄 Licence

Projet SmartContractDevPipeline - Usage interne
