# agents/smart_contract/sous_agents/security_expert.ps1
Write-Host "Création du Sous-Agent Sécurité Smart Contract..." -ForegroundColor Cyan

$securityAgentConfig = @'
# agents/smart_contract/sous_agents/security_config.yaml
sous_agent_id: "security_expert_001"
parent_agent: "smart_contract"
specialization: "Sécurité des Smart Contracts"
model: "ollama:deepseek-coder:6.7b"
temperature: 0.05

capabilities:
  vulnerability_detection:
    - "Reentrancy"
    - "Integer Overflow/Underflow"
    - "Access Control Issues"
    - "Unchecked External Calls"
    - "Front Running"
    - "Timestamp Dependence"
  security_tools:
    - "Slither"
    - "Mythril"
    - "Manticore"
    - "Echidna"
    - "Solhint"
  testing_methodologies:
    - "Fuzzing"
    - "Formal Verification"
    - "Symbolic Execution"
    - "Property-Based Testing"
  standards:
    - "SWC Registry"
    - "EIP Standards"
    - "Security Best Practices"

tools:
  - name: "vulnerability_scanner"
    type: "security_scanner"
    version: "1.0.0"
    
  - name: "exploit_generator"
    type: "exploit_simulator"
    version: "1.0.0"
    
  - name: "remediation_suggester"
    type: "fix_generator"
    version: "1.0.0"

context_requirements:
  contract_complexity: "Complexité du contrat"
  value_at_risk: "Valeur protégée par le contrat"
  attack_vectors: "Vecteurs d'attaque potentiels"
  compliance_requirements: "Exigences de conformité"

outputs:
  required:
    - security_audit_report.md
    - vulnerability_assessment.json
    - remediation_plan.md
    - security_test_cases/
  optional:
    - exploit_pocs/
    - formal_verification_proofs/
    - security_monitoring_rules/

learning_objectives:
  - "Détecter les nouvelles vulnérabilités"
  - "Générer des exploits de test"
  - "Proposer des correctifs sécurisés"
  - "Améliorer les méthodologies de test"
'@

$securityAgentConfig | Out-File -FilePath "$projectPath\agents\smart_contract\sous_agents\security_config.yaml" -Force -Encoding UTF8