# agents/coder/sous_agents/devops_coder.ps1
Write-Host "Création du Sous-Agent DevOps..." -ForegroundColor Cyan

$devopsAgentConfig = @'
# agents/coder/sous_agents/devops_config.yaml
sous_agent_id: "devops_coder_001"
parent_agent: "coder"
specialization: "DevOps & Infrastructure as Code"
model: "ollama:llama3.2:3b"
temperature: 0.2

capabilities:
  ci_cd:
    - "GitHub Actions"
    - "GitLab CI"
    - "Jenkins"
    - "CircleCI"
  iac_tools:
    - "Terraform"
    - "Pulumi"
    - "CloudFormation"
    - "Ansible"
  containerization:
    - "Docker"
    - "Podman"
    - "Buildah"
  orchestration:
    - "Kubernetes"
    - "Docker Swarm"
    - "Nomad"
  monitoring:
    - "Prometheus"
    - "Grafana"
    - "ELK Stack"
    - "Datadog"

tools:
  - name: "pipeline_generator"
    type: "ci_cd_generator"
    version: "1.0.0"
    
  - name: "terraform_generator"
    type: "iac_generator"
    version: "1.0.0"
    
  - name: "monitoring_setup"
    type: "observability_setup"
    version: "1.0.0"

context_requirements:
  deployment_targets: "Environnements de déploiement"
  scaling_requirements: "Exigences de scalabilité"
  security_requirements: "Exigences de sécurité"
  compliance_requirements: "Exigences de conformité"

outputs:
  required:
    - ci_cd_pipelines/
    - infrastructure_code/
    - docker_configs/
    - monitoring_configs/
  optional:
    - security_scans/
    - backup_strategies/
    - disaster_recovery/

learning_objectives:
  - "Automatiser les déploiements"
  - "Optimiser les coûts infrastructure"
  - "Renforcer la sécurité DevOps"
  - "Améliorer l'observabilité"
'@

$devopsAgentConfig | Out-File -FilePath "$projectPath\agents\coder\sous_agents\devops_config.yaml" -Force -Encoding UTF8