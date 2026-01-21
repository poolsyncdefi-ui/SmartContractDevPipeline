# deploy-subagents.ps1
Write-Host "=== DEPLOIEMENT COMPLET DES SOUS-AGENTS ===" -ForegroundColor Cyan
Write-Host "Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

$projectPath = "$env:USERPROFILE\Projects\SmartContractPipeline"
Set-Location $projectPath

# Liste de tous les sous-agents à créer
$subAgents = @(
    @{Parent="architect"; Name="cloud_architect"; Type="Cloud Architecture"},
    @{Parent="architect"; Name="blockchain_architect"; Type="Blockchain Architecture"},
    @{Parent="architect"; Name="microservices_architect"; Type="Microservices Architecture"},
    
    @{Parent="coder"; Name="backend_coder"; Type="Backend Development"},
    @{Parent="coder"; Name="frontend_coder"; Type="Frontend Development"},
    @{Parent="coder"; Name="devops_coder"; Type="DevOps"},
    
    @{Parent="smart_contract"; Name="solidity_expert"; Type="Solidity Development"},
    @{Parent="smart_contract"; Name="security_expert"; Type="Smart Contract Security"},
    @{Parent="smart_contract"; Name="gas_optimizer"; Type="Gas Optimization"},
    @{Parent="smart_contract"; Name="formal_verification"; Type="Formal Verification"},
    
    @{Parent="frontend_web3"; Name="react_expert"; Type="React/Next.js"},
    @{Parent="frontend_web3"; Name="web3_integration"; Type="Web3 Integration"},
    @{Parent="frontend_web3"; Name="ui_ux_expert"; Type="UI/UX Design"},
    
    @{Parent="tester"; Name="unit_tester"; Type="Unit Testing"},
    @{Parent="tester"; Name="integration_tester"; Type="Integration Testing"},
    @{Parent="tester"; Name="e2e_tester"; Type="E2E Testing"},
    @{Parent="tester"; Name="fuzzing_expert"; Type="Fuzzing"}
)

Write-Host "1. CREATION DE LA STRUCTURE DES SOUS-AGENTS..." -ForegroundColor Yellow

foreach ($subAgent in $subAgents) {
    $parentDir = "$projectPath\agents\$($subAgent.Parent)\sous_agents"
    $agentDir = "$parentDir\$($subAgent.Name)"
    
    # Créer le dossier du sous-agent
    New-Item -ItemType Directory -Path $agentDir -Force | Out-Null
    
    # Créer les fichiers de base
    $files = @("config.yaml", "agent.py", "tools.py", "__init__.py")
    foreach ($file in $files) {
        $filePath = "$agentDir\$file"
        if (-not (Test-Path $filePath)) {
            New-Item -ItemType File -Path $filePath -Force | Out-Null
        }
    }
    
    Write-Host "   ✅ $($subAgent.Parent)/$($subAgent.Name) ($($subAgent.Type))" -ForegroundColor Green
}

# 2. Créer les fichiers __init__.py pour l'import
Write-Host "`n2. CONFIGURATION DES IMPORTS..." -ForegroundColor Yellow

foreach ($parent in @("architect", "coder", "smart_contract", "frontend_web3", "tester")) {
    $initFile = "$projectPath\agents\$parent\sous_agents\__init__.py"
    
    $imports = @'
# Import des sous-agents
try:
    from .cloud_architect import CloudArchitectSubAgent
    from .blockchain_architect import BlockchainArchitectSubAgent
    from .microservices_architect import MicroservicesArchitectSubAgent
except ImportError as e:
    print(f"Erreur d'import des sous-agents: {e}")

__all__ = [
    "CloudArchitectSubAgent",
    "BlockchainArchitectSubAgent", 
    "MicroservicesArchitectSubAgent"
]
'@
    
    # Adapter les imports selon le parent
    if ($parent -eq "coder") {
        $imports = $imports.Replace("cloud_architect", "backend_coder")
        $imports = $imports.Replace("blockchain_architect", "frontend_coder")
        $imports = $imports.Replace("microservices_architect", "devops_coder")
        $imports = $imports.Replace("CloudArchitectSubAgent", "BackendCoderSubAgent")
        $imports = $imports.Replace("BlockchainArchitectSubAgent", "FrontendCoderSubAgent")
        $imports = $imports.Replace("MicroservicesArchitectSubAgent", "DevOpsCoderSubAgent")
    }
    
    $imports | Out-File -FilePath $initFile -Force -Encoding UTF8
    Write-Host "   ✅ $parent/__init__.py créé" -ForegroundColor Green
}

# 3. Mettre à jour l'agent parent pour gérer les sous-agents
Write-Host "`n3. MISE A JOUR DES AGENTS PARENTS..." -ForegroundColor Yellow

foreach ($parent in @("architect", "coder", "smart_contract", "frontend_web3", "tester")) {
    $parentAgentFile = "$projectPath\agents\$parent\agent.py"
    
    if (Test-Path $parentAgentFile) {
        $parentCode = Get-Content $parentAgentFile -Raw
        
        # Ajouter la gestion des sous-agents
        $subAgentManagement = @'

    # Gestion des sous-agents
    def __init__(self, config_path: str):
        super().__init__(config_path)
        self.sub_agents = {}
        self._initialize_sub_agents()
    
    def _initialize_sub_agents(self):
        """Initialise les sous-agents spécialisés"""
        try:
            from .sous_agents import *
            
            # Création dynamique des sous-agents basée sur la configuration
            sub_agent_configs = self.config.get("sub_agents", {})
            
            for agent_name, agent_config in sub_agent_configs.items():
                agent_class_name = f"{agent_name.capitalize().replace('_', '')}SubAgent"
                agent_class = globals().get(agent_class_name)
                
                if agent_class:
                    sub_agent = agent_class(agent_config.get("config_path", ""))
                    self.sub_agents[agent_name] = sub_agent
                    self.logger.info(f"Sous-agent {agent_name} initialisé")
                else:
                    self.logger.warning(f"Classe non trouvée pour le sous-agent {agent_name}")
                    
        except ImportError as e:
            self.logger.error(f"Erreur lors de l'import des sous-agents: {e}")
    
    async def delegate_to_sub_agent(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Délègue une tâche à un sous-agent approprié"""
        # Logique de routage vers le bon sous-agent
        sub_agent_mapping = self.config.get("sub_agent_mapping", {})
        
        for pattern, agent_name in sub_agent_mapping.items():
            if task_type.startswith(pattern):
                if agent_name in self.sub_agents:
                    self.logger.info(f"Délégation de la tâche {task_type} au sous-agent {agent_name}")
                    return await self.sub_agents[agent_name].execute(task_data, {})
        
        # Fallback: utiliser l'agent principal
        self.logger.info(f"Aucun sous-agent trouvé pour {task_type}, utilisation de l'agent principal")
        return await self.execute(task_data, {})
    
    async def get_sub_agents_status(self) -> Dict[str, Any]:
        """Retourne le statut de tous les sous-agents"""
        status = {}
        
        for agent_name, agent_instance in self.sub_agents.items():
            try:
                health = await agent_instance.health_check()
                status[agent_name] = {
                    "status": health.get("status", "unknown"),
                    "agent_info": agent_instance.get_agent_info()
                }
            except Exception as e:
                status[agent_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return {
            "total_sub_agents": len(self.sub_agents),
            "sub_agents": status
        }
'@
        
        # Insérer après la classe BaseAgent
        if ($parentCode -match "class.*Agent\(BaseAgent\):") {
            $modifiedCode = $parentCode -replace "(class.*Agent\(BaseAgent\):[\s\S]*?)(def __init__)", "`$1$subAgentManagement`n`n    `$2"
            $modifiedCode | Out-File -FilePath $parentAgentFile -Force -Encoding UTF8
            Write-Host "   ✅ $parent/agent.py mis à jour avec la gestion des sous-agents" -ForegroundColor Green
        }
    }
}

# 4. Créer les configurations de mapping
Write-Host "`n4. CREATION DES CONFIGURATIONS DE MAPPING..." -ForegroundColor Yellow

foreach ($parent in @("architect", "coder", "smart_contract", "frontend_web3", "tester")) {
    $configFile = "$projectPath\agents\$parent\config.yaml"
    
    if (Test-Path $configFile) {
        $configContent = Get-Content $configFile -Raw
        
        # Ajouter la section sub_agents
        $subAgentSection = @'
# Configuration des sous-agents
sub_agents:
  cloud_architect:
    enabled: true
    config_path: "agents/architect/sous_agents/cloud_config.yaml"
    specialization: "Architecture Cloud"
  blockchain_architect:
    enabled: true
    config_path: "agents/architect/sous_agents/blockchain_config.yaml"
    specialization: "Architecture Blockchain"
  microservices_architect:
    enabled: true
    config_path: "agents/architect/sous_agents/microservices_config.yaml"
    specialization: "Architecture Microservices"

# Mapping des tâches vers les sous-agents
sub_agent_mapping:
  "cloud_": "cloud_architect"
  "aws_": "cloud_architect"
  "azure_": "cloud_architect"
  "gcp_": "cloud_architect"
  "blockchain_": "blockchain_architect"
  "web3_": "blockchain_architect"
  "smart_contract_": "blockchain_architect"
  "microservices_": "microservices_architect"
  "service_": "microservices_architect"
  "api_": "microservices_architect"
'@
        
        # Adapter pour chaque parent
        if ($parent -eq "coder") {
            $subAgentSection = $subAgentSection.Replace("cloud_architect", "backend_coder")
            $subAgentSection = $subAgentSection.Replace("blockchain_architect", "frontend_coder")
            $subAgentSection = $subAgentSection.Replace("microservices_architect", "devops_coder")
            $subAgentSection = $subAgentSection.Replace("Architecture Cloud", "Backend Development")
            $subAgentSection = $subAgentSection.Replace("Architecture Blockchain", "Frontend Development")
            $subAgentSection = $subAgentSection.Replace("Architecture Microservices", "DevOps")
            $subAgentSection = $subAgentSection.Replace("cloud_", "backend_")
            $subAgentSection = $subAgentSection.Replace("aws_", "api_")
            $subAgentSection = $subAgentSection.Replace("azure_", "database_")
            $subAgentSection = $subAgentSection.Replace("gcp_", "infrastructure_")
            $subAgentSection = $subAgentSection.Replace("blockchain_", "frontend_")
            $subAgentSection = $subAgentSection.Replace("web3_", "ui_")
            $subAgentSection = $subAgentSection.Replace("smart_contract_", "component_")
            $subAgentSection = $subAgentSection.Replace("microservices_", "devops_")
            $subAgentSection = $subAgentSection.Replace("service_", "pipeline_")
            $subAgentSection = $subAgentSection.Replace("api_", "deployment_")
        }
        
        # Ajouter à la fin du fichier
        $newContent = $configContent.Trim() + "`n`n" + $subAgentSection
        $newContent | Out-File -FilePath $configFile -Force -Encoding UTF8
        
        Write-Host "   ✅ $parent/config.yaml mis à jour avec le mapping des sous-agents" -ForegroundColor Green
    }
}

# 5. Tester l'intégration des sous-agents
Write-Host "`n5. TEST DE L'INTEGRATION..." -ForegroundColor Yellow

$testIntegrationScript = @'
# test_subagents_integration.py
import asyncio
import sys
from pathlib import Path

# Ajouter le dossier agents au path
agents_dir = Path(__file__).parent / "agents"
sys.path.insert(0, str(agents_dir))

async def test_subagents():
    """Teste l'intégration des sous-agents"""
    print("🧪 TEST D'INTEGRATION DES SOUS-AGENTS")
    print("="*60)
    
    # Test avec l'agent architecte
    try:
        from architect.agent import ArchitectAgent
        
        # Créer l'agent
        architect = ArchitectAgent("agents/architect/config.yaml")
        await architect.initialize()
        
        print(f"✅ Agent architecte initialisé")
        print(f"📊 Sous-agents chargés: {len(architect.sub_agents)}")
        
        # Tester chaque sous-agent
        for agent_name, agent_instance in architect.sub_agents.items():
            try:
                info = agent_instance.get_agent_info()
                print(f"  • {agent_name}: {info.get('specialization', 'N/A')}")
            except Exception as e:
                print(f"  • {agent_name}: ❌ Erreur - {e}")
        
        # Tester la délégation
        test_task = {
            "type": "cloud_design",
            "requirements": {
                "name": "Test Cloud Architecture",
                "budget_constrained": True,
                "needs_global_presence": False
            }
        }
        
        result = await architect.delegate_to_sub_agent("cloud_design", test_task)
        print(f"📋 Résultat de délégation: {result.get('status', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    
    print("="*60)
    print("✅ TEST D'INTEGRATION TERMINE")

if __name__ == "__main__":
    asyncio.run(test_subagents())
'@

$testIntegrationScript | Out-File -FilePath "$projectPath\test_subagents_integration.py" -Force -Encoding UTF8

try {
    & "$projectPath\.venv\Scripts\Activate.ps1"
    python "$projectPath\test_subagents_integration.py"
    Write-Host "   ✅ Test d'intégration réussi" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Erreur lors du test d'intégration: $_" -ForegroundColor Yellow
}

# 6. Générer le rapport final
Write-Host "`n6. GENERATION DU RAPPORT FINAL..." -ForegroundColor Yellow

$subAgentsReport = @{
    deployment_date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    total_sub_agents = $subAgents.Count
    sub_agents_by_parent = @{}
    structure = @{}
}

foreach ($parent in @("architect", "coder", "smart_contract", "frontend_web3", "tester")) {
    $parentSubAgents = $subAgents | Where-Object { $_.Parent -eq $parent }
    $subAgentsReport.sub_agents_by_parent[$parent] = @{
        count = $parentSubAgents.Count
        agents = $parentSubAgents.Name
        types = $parentSubAgents.Type
    }
    
    # Compter les fichiers créés
    $parentDir = "$projectPath\agents\$parent\sous_agents"
    if (Test-Path $parentDir) {
        $fileCount = (Get-ChildItem -Path $parentDir -File -Recurse).Count
        $dirCount = (Get-ChildItem -Path $parentDir -Directory).Count
        $subAgentsReport.structure[$parent] = @{
            directories = $dirCount
            files = $fileCount
        }
    }
}

$subAgentsReport | ConvertTo-Json -Depth 10 | Out-File -FilePath "$projectPath\reports\subagents_deployment_report.json" -Force

Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "🎉 DEPLOIEMENT DES SOUS-AGENTS TERMINE !" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 RESUME:" -ForegroundColor Yellow
Write-Host "  • Sous-agents déployés: $($subAgentsReport.total_sub_agents)" -ForegroundColor White
Write-Host ""
Write-Host "🔧 PAR AGENT PRINCIPAL:" -ForegroundColor Yellow
foreach ($parent in $subAgentsReport.sub_agents_by_parent.Keys) {
    $parentData = $subAgentsReport.sub_agents_by_parent[$parent]
    Write-Host "  • $parent : $($parentData.count) sous-agents" -ForegroundColor White
    foreach ($agent in $parentData.agents) {
        Write-Host "    ◦ $agent" -ForegroundColor Gray
    }
}
Write-Host ""
Write-Host "📁 FICHIERS CREES:" -ForegroundColor Yellow
foreach ($parent in $subAgentsReport.structure.Keys) {
    $structure = $subAgentsReport.structure[$parent]
    Write-Host "  • $parent : $($structure.files) fichiers dans $($structure.directories) dossiers" -ForegroundColor White
}
Write-Host ""
Write-Host "⚡ COMMANDES DE TEST:" -ForegroundColor Yellow
Write-Host "  Tester l'intégration: python test_subagents_integration.py" -ForegroundColor White
Write-Host "  Voir le rapport: cat reports\subagents_deployment_report.json" -ForegroundColor White
Write-Host "  Lister tous les agents: Get-ChildItem agents\*\sous_agents\*" -ForegroundColor White
Write-Host ""
Write-Host "✅ ARCHITECTURE HIERARCHIQUE COMPLETE" -ForegroundColor Green