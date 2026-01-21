# agents/frontend_web3/sous_agents/web3_integration.ps1
Write-Host "Création du Sous-Agent Web3 Integration..." -ForegroundColor Cyan

$web3IntegrationConfig = @'
# agents/frontend_web3/sous_agents/web3_integration_config.yaml
sous_agent_id: "web3_integration_001"
parent_agent: "frontend_web3"
specialization: "Intégration Web3 & Wallet"
model: "ollama:deepseek-coder:6.7b"
temperature: 0.2

capabilities:
  web3_libraries:
    - "wagmi"
    - "viem"
    - "ethers.js"
    - "web3.js"
  wallet_integration:
    - "MetaMask"
    - "WalletConnect"
    - "Coinbase Wallet"
    - "RainbowKit"
  contract_interaction:
    - "ABI Integration"
    - "Event Listening"
    - "Transaction Building"
    - "Error Handling"
  network_management:
    - "Multi-Chain Support"
    - "Network Switching"
    - "RPC Management"
    - "Chain Agnostic Design"

tools:
  - name: "hook_generator"
    type: "web3_hook_generator"
    version: "1.0.0"
    
  - name: "provider_setup"
    type: "web3_provider_setup"
    version: "1.0.0"
    
  - name: "transaction_builder"
    type: "tx_builder"
    version: "1.0.0"

context_requirements:
  supported_chains: "Chains supportées"
  wallet_requirements: "Exigences wallet"
  contract_interactions: "Interactions avec les contrats"
  user_experience: "Expérience utilisateur visée"

outputs:
  required:
    - web3_providers/
    - custom_hooks/
    - transaction_handlers/
    - wallet_connectors/
  optional:
    - multi_chain_support/
    - transaction_monitoring/
    - gas_estimation/

learning_objectives:
  - "Gérer les connexions wallet"
  - "Construire des transactions"
  - "Gérer les erreurs Web3"
  - "Optimiser l'expérience utilisateur"
'@

$web3IntegrationConfig | Out-File -FilePath "$projectPath\agents\frontend_web3\sous_agents\web3_integration_config.yaml" -Force -Encoding UTF8