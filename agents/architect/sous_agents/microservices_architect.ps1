# agents/architect/sous_agents/microservices_architect.ps1
Write-Host "Création du Sous-Agent Architecture Microservices..." -ForegroundColor Cyan

$microservicesAgentConfig = @'
# agents/architect/sous_agents/microservices_config.yaml
sous_agent_id: "microservices_architect_001"
parent_agent: "architect"
specialization: "Architecture Microservices & Event-Driven"
model: "ollama:llama3.1:8b"
temperature: 0.3

capabilities:
  communication_patterns:
    - "Synchronous (REST, gRPC)"
    - "Asynchronous (Message Queues, Event Streaming)"
    - "Event Sourcing"
    - "CQRS"
  service_discovery:
    - "Consul"
    - "Eureka"
    - "Kubernetes DNS"
  api_gateways:
    - "Kong"
    - "Traefik"
    - "NGINX"
  message_brokers:
    - "RabbitMQ"
    - "Kafka"
    - "NATS"
    - "Redis Pub/Sub"

tools:
  - name: "service_boundary_designer"
    type: "domain_design"
    version: "1.0.0"
    
  - name: "event_storming_facilitator"
    type: "event_modeling"
    version: "1.0.0"
    
  - name: "resilience_pattern_applier"
    type: "circuit_breaker"
    version: "1.0.0"

context_requirements:
  domain_complexity: "Complexité du domaine métier"
  team_structure: "Structure des équipes de développement"
  expected_scale: "Échelle prévue du système"
  data_consistency_needs: "Besoins en cohérence des données"

outputs:
  required:
    - bounded_contexts.json
    - event_storming_diagram.mmd
    - api_specifications/
    - service_contracts/
  optional:
    - deployment_pipeline_design.md
    - observability_strategy.md
    - disaster_recovery_plan.md

learning_objectives:
  - "Identifier les bounded contexts"
  - "Design des contrats de service"
  - "Implémenter les patterns de résilience"
  - "Optimiser la communication inter-services"
'@

$microservicesAgentConfig | Out-File -FilePath "$projectPath\agents\architect\sous_agents\microservices_config.yaml" -Force -Encoding UTF8