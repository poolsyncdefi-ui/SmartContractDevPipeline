# agents/architect/sous_agents/blockchain_architect.ps1
Write-Host "Création du Sous-Agent Architecture Blockchain..." -ForegroundColor Cyan

$blockchainAgentConfig = @'
# agents/architect/sous_agents/blockchain_config.yaml
sous_agent_id: "blockchain_architect_001"
parent_agent: "architect"
specialization: "Architecture Blockchain & Web3"
model: "ollama:deepseek-coder:6.7b"
temperature: 0.2

capabilities:
  blockchain_platforms:
    - "Ethereum (EVM)"
    - "Polygon"
    - "Arbitrum"
    - "Optimism"
    - "Solana"
    - "Avalanche"
  consensus_mechanisms:
    - "Proof of Stake"
    - "Proof of Work"
    - "Proof of Authority"
  scaling_solutions:
    - "Layer 2 (Rollups)"
    - "Sidechains"
    - "State Channels"
    - "Plasma"
  storage_solutions:
    - "IPFS"
    - "Arweave"
    - "Filecoin"
    - "Ceramic"

tools:
  - name: "smart_contract_analyzer"
    type: "contract_architecture"
    version: "1.0.0"
    
  - name: "gas_optimizer"
    type: "gas_analysis"
    version: "1.0.0"
    
  - name: "network_selector"
    type: "blockchain_selector"
    version: "1.0.0"

context_requirements:
  transaction_volume: "TPS requis"
  security_level: "Niveau de sécurité nécessaire"
  decentralization_level: "Degré de décentralisation"
  token_economics: "Économie de tokens"

outputs:
  required:
    - blockchain_architecture_diagram.mmd
    - network_selection_report.md
    - smart_contract_architecture.md
    - gas_optimization_plan.md
  optional:
    - tokenomics_model.json
    - governance_structure.md
    - upgradeability_plan.md

learning_objectives:
  - "Optimiser les coûts de gas"
  - "Améliorer la scalabilité"
  - "Renforcer la sécurité on-chain"
  - "Design des mécanismes de gouvernance"
'@

$blockchainAgentConfig | Out-File -FilePath "$projectPath\agents\architect\sous_agents\blockchain_config.yaml" -Force -Encoding UTF8