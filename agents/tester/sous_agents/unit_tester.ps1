# agents/tester/sous_agents/unit_tester.ps1
Write-Host "Création du Sous-Agent Test Unitaires..." -ForegroundColor Cyan

$unitTesterConfig = @'
# agents/tester/sous_agents/unit_test_config.yaml
sous_agent_id: "unit_tester_001"
parent_agent: "tester"
specialization: "Tests Unitaires & Coverage"
model: "ollama:qwen2.5:7b"
temperature: 0.3

capabilities:
  testing_frameworks:
    - "pytest (Python)"
    - "Jest (JavaScript)"
    - "Mocha/Chai (JavaScript)"
    - "Foundry Test (Solidity)"
  mocking:
    - "unittest.mock (Python)"
    - "Jest Mock (JavaScript)"
    - "Mockito (Java)"
  coverage_tools:
    - "coverage.py"
    - "Istanbul"
    - "lcov"
  assertion_libraries:
    - "assert"
    - "chai"
    - "assertpy"

tools:
  - name: "test_generator"
    type: "unit_test_generator"
    version: "1.0.0"
    
  - name: "coverage_analyzer"
    type: "coverage_analyzer"
    version: "1.0.0"
    
  - name: "mock_generator"
    type: "mock_generator"
    version: "1.0.0"

context_requirements:
  codebase_language: "Langage du codebase"
  complexity_level: "Niveau de complexité"
  coverage_target: "Cible de couverture"
  testing_strategy: "Stratégie de test"

outputs:
  required:
    - unit_tests/
    - coverage_report/
    - test_results.json
    - mock_objects/
  optional:
    - benchmark_tests/
    - performance_tests/
    - integration_tests/

learning_objectives:
  - "Augmenter la couverture de tests"
  - "Générer des mocks efficaces"
  - "Détecter les edge cases"
  - "Optimiser l'exécution des tests"
'@

$unitTesterConfig | Out-File -FilePath "$projectPath\agents\tester\sous_agents\unit_test_config.yaml" -Force -Encoding UTF8