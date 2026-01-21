# agents/coder/sous_agents/frontend_coder.ps1
Write-Host "Création du Sous-Agent Code Frontend..." -ForegroundColor Cyan

$frontendCoderConfig = @'
# agents/coder/sous_agents/frontend_config.yaml
sous_agent_id: "frontend_coder_001"
parent_agent: "coder"
specialization: "Développement Frontend & UI"
model: "ollama:deepseek-coder:6.7b"
temperature: 0.3

capabilities:
  frameworks:
    - "React (Next.js, Remix)"
    - "Vue.js (Nuxt.js)"
    - "Angular"
    - "Svelte (SvelteKit)"
  styling:
    - "Tailwind CSS"
    - "Styled Components"
    - "CSS Modules"
    - "Sass/SCSS"
  state_management:
    - "Redux Toolkit"
    - "Zustand"
    - "MobX"
    - "Context API"
  testing:
    - "Jest"
    - "React Testing Library"
    - "Cypress"
    - "Playwright"

tools:
  - name: "component_generator"
    type: "ui_component_generator"
    version: "1.0.0"
    
  - name: "state_manager"
    type: "state_management_designer"
    version: "1.0.0"
    
  - name: "performance_analyzer"
    type: "frontend_performance"
    version: "1.0.0"

context_requirements:
  design_system: "Système de design à suivre"
  responsive_requirements: "Exigences responsive"
  accessibility_requirements: "Exigences d'accessibilité"
  browser_support: "Navigateurs à supporter"

outputs:
  required:
    - component_library/
    - page_templates/
    - state_management/
    - unit_tests/
  optional:
    - e2e_tests/
    - performance_reports/
    - accessibility_reports/

learning_objectives:
  - "Optimiser le bundle size"
  - "Améliorer les Core Web Vitals"
  - "Implémenter l'accessibilité"
  - "Design des composants réutilisables"
'@

$frontendCoderConfig | Out-File -FilePath "$projectPath\agents\coder\sous_agents\frontend_config.yaml" -Force -Encoding UTF8