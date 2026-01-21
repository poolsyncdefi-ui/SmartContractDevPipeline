# agents/smart_contract/sous_agents/gas_optimizer.ps1
Write-Host "Création du Sous-Agent Gas Optimizer..." -ForegroundColor Cyan

$gasOptimizerConfig = @'
# agents/smart_contract/sous_agents/gas_config.yaml
sous_agent_id: "gas_optimizer_001"
parent_agent: "smart_contract"
specialization: "Optimisation des Coûts de Gas"
model: "ollama:deepseek-coder:6.7b"
temperature: 0.1

capabilities:
  optimization_techniques:
    - "Storage Packing"
    - "Memory vs Storage"
    - "Assembly Optimization"
    - "Function Inlining"
    - "Loop Optimization"
    - "Constant Propagation"
  gas_profiling:
    - "Transaction Gas Analysis"
    - "Contract Deployment Gas"
    - "Function Call Gas"
    - "Storage Operation Gas"
  optimization_tools:
    - "Foundry Gas Reports"
    - "Hardhat Gas Reporter"
    - "EVM Opcode Analysis"
    - "Gas Profiling Scripts"

tools:
  - name: "gas_profiler"
    type: "gas_analyzer"
    version: "1.0.0"
    
  - name: "optimization_suggester"
    type: "gas_optimization_suggester"
    version: "1.0.0"
    
  - name: "assembly_generator"
    type: "evm_assembly_generator"
    version: "1.0.0"

context_requirements:
  contract_size: "Taille actuelle du contrat"
  gas_usage_patterns: "Patterns d'utilisation du gas"
  optimization_targets: "Cibles d'optimisation"
  budget_constraints: "Contraintes budgétaires"

outputs:
  required:
    - gas_analysis_report.md
    - optimization_suggestions.json
    - optimized_contract_code.sol
    - gas_savings_calculation.md
  optional:
    - assembly_optimizations/
    - benchmark_results/
    - cost_projection/

learning_objectives:
  - "Réduire les coûts de déploiement"
  - "Optimiser les transactions courantes"
  - "Apprendre les techniques d'assembly"
  - "Analyser les opcodes EVM"
'@

$gasOptimizerConfig | Out-File -FilePath "$projectPath\agents\smart_contract\sous_agents\gas_config.yaml" -Force -Encoding UTF8