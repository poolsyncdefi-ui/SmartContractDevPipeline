# agents/frontend_web3/sous_agents/react_expert.ps1
Write-Host "Création du Sous-Agent React/Next.js..." -ForegroundColor Cyan

$reactAgentConfig = @'
# agents/frontend_web3/sous_agents/react_config.yaml
sous_agent_id: "react_expert_001"
parent_agent: "frontend_web3"
specialization: "Développement React/Next.js Avancé"
model: "ollama:deepseek-coder:6.7b"
temperature: 0.3

capabilities:
  react_features:
    - "React 18 (Concurrent Features)"
    - "Server Components"
    - "Server Actions"
    - "Suspense & Streaming"
  nextjs_features:
    - "App Router"
    - "Server-Side Rendering"
    - "Static Site Generation"
    - "Incremental Static Regeneration"
  performance:
    - "Code Splitting"
    - "Lazy Loading"
    - "Image Optimization"
    - "Bundle Optimization"
  state_management:
    - "React Context"
    - "Zustand"
    - "Redux Toolkit"
    - "React Query"

tools:
  - name: "component_generator"
    type: "react_component_generator"
    version: "1.0.0"
    
  - name: "page_generator"
    type: "nextjs_page_generator"
    version: "1.0.0"
    
  - name: "performance_optimizer"
    type: "react_performance_optimizer"
    version: "1.0.0"

context_requirements:
  project_scale: "Échelle du projet"
  seo_requirements: "Exigences SEO"
  performance_targets: "Cibles de performance"
  accessibility_requirements: "Exigences d'accessibilité"

outputs:
  required:
    - components/
    - pages/
    - hooks/
    - utils/
  optional:
    - middleware/
    - api_routes/
    - static_assets/

learning_objectives:
  - "Optimiser le Core Web Vitals"
  - "Implémenter le Server Components"
  - "Améliorer le SEO"
  - "Gérer le state efficacement"
'@

$reactAgentConfig | Out-File -FilePath "$projectPath\agents\frontend_web3\sous_agents\react_config.yaml" -Force -Encoding UTF8