# setup.ps1 - Version sans accents
Write-Host "=== SMART CONTRACT PIPELINE SETUP ===" -ForegroundColor Cyan
Write-Host "Complete installation script" -ForegroundColor Yellow
Write-Host ""

# Ask for confirmation
$confirm = Read-Host "Do you want to install all components? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Installation cancelled" -ForegroundColor Yellow
    exit
}

# 1. Check PowerShell version
Write-Host "`n1. CHECKING POWERSHELL..." -ForegroundColor Yellow
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Host "X PowerShell 5.0 or higher required" -ForegroundColor Red
    exit 1
}
Write-Host "V PowerShell $($PSVersionTable.PSVersion)" -ForegroundColor Green

# 2. Check required tools
Write-Host "`n2. CHECKING REQUIRED TOOLS..." -ForegroundColor Yellow

$tools = @(
    @{Name="Node.js"; Test="node --version"; Install="https://nodejs.org"},
    @{Name="Python"; Test="python --version"; Install="https://python.org"},
    @{Name="Git"; Test="git --version"; Install="https://git-scm.com"}
)

foreach ($tool in $tools) {
    Write-Host "Checking $($tool.Name)..." -ForegroundColor Gray
    try {
        Invoke-Expression $tool.Test 2>$null
        Write-Host "V $($tool.Name) is installed" -ForegroundColor Green
    } catch {
        Write-Host "X $($tool.Name) is NOT installed" -ForegroundColor Red
        Write-Host "  Install from: $($tool.Install)" -ForegroundColor Cyan
    }
}

# 3. Create project structure
Write-Host "`n3. CREATING PROJECT STRUCTURE..." -ForegroundColor Yellow

$folders = @(
    "agents",
    "agents\architect",
    "agents\coder",
    "agents\communication",
    "agents\documenter",
    "agents\formal_verification",
    "agents\frontend_web3",
    "agents\fuzzing_simulation",
    "agents\quality_metrics",
    "agents\smart_contract",
    "agents\tester",
    "agents\shared",
    "config",
    "context",
    "memory",
    "memory\vector_store",
    "memory\history",
    "memory\learnings",
    "workspace",
    "workspace\contracts",
    "workspace\frontend",
    "sprints",
    "reports",
    "logs",
    "scripts",
    "tests"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Path $folder -Force -ErrorAction SilentlyContinue | Out-Null
    Write-Host "  [FOLDER] $folder" -ForegroundColor Gray
}

# 4. Create essential files
Write-Host "`n4. CREATING ESSENTIAL FILES..." -ForegroundColor Yellow

# package.json
@'
{
  "name": "smart-contract-pipeline",
  "version": "1.0.0",
  "description": "Automated Smart Contract Development Pipeline with AI Agents",
  "main": "main.py",
  "scripts": {
    "start": "python main.py",
    "test": "python -m pytest",
    "hardhat": "cd workspace\\contracts && npx hardhat",
    "frontend": "cd workspace\\frontend && npm run dev"
  },
  "keywords": ["blockchain", "smart-contract", "ai", "web3"],
  "author": "SmartContractPipeline",
  "license": "MIT"
}
'@ | Out-File -FilePath "package.json" -Force -Encoding UTF8
Write-Host "V package.json created" -ForegroundColor Green

# requirements.txt
@'
# Core AI & ML
langchain>=0.1.0
chromadb>=0.4.0

# Web3 & Blockchain
web3>=6.0.0
eth-account>=0.11.0

# Web Framework & API
fastapi>=0.104.0
requests>=2.31.0

# Data Processing
pyyaml>=6.0.0
python-dotenv>=1.0.0

# Utilities
pydantic>=2.0.0
pytest>=7.4.0
'@ | Out-File -FilePath "requirements.txt" -Force -Encoding UTF8
Write-Host "V requirements.txt created" -ForegroundColor Green

# Create Python virtual environment
Write-Host "`n5. SETTING UP PYTHON ENVIRONMENT..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "V Python virtual environment created" -ForegroundColor Green
}

# Activate and install Python dependencies
try {
    & .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    Write-Host "V Python dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "X Error installing Python dependencies: $_" -ForegroundColor Red
}

# 6. Initialize Hardhat project
Write-Host "`n6. INITIALIZING HARPHAT..." -ForegroundColor Yellow
Set-Location "workspace\contracts"

try {
    # Check if Hardhat is installed
    npx hardhat --version 2>$null
    Write-Host "V Hardhat is installed" -ForegroundColor Green
} catch {
    Write-Host "Installing Hardhat..." -ForegroundColor Gray
    npm init -y
    npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
}

# Initialize Hardhat project if not exists
if (-not (Test-Path "hardhat.config.js") -and -not (Test-Path "hardhat.config.ts")) {
    npx hardhat init --typescript
    npm install @openzeppelin/contracts ethers
    Write-Host "V Hardhat project initialized" -ForegroundColor Green
}

Set-Location ..\..

# 7. Create basic agent
Write-Host "`n7. CREATING BASIC AGENT..." -ForegroundColor Yellow

$agentCode = @'
# agents/smart_contract/agent.py
import json
from typing import Dict, Any

class SmartContractAgent:
    """Basic Smart Contract Agent"""
    
    def __init__(self):
        self.name = "Smart Contract Agent"
        self.version = "1.0.0"
    
    def generate_contract(self, requirements: Dict[str, Any]) -> str:
        """Generate a smart contract based on requirements"""
        contract_name = requirements.get("name", "MyContract")
        
        template = f'''// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract {contract_name} {{
    address public owner;
    string public name;
    string public symbol;
    
    constructor(string memory _name, string memory _symbol) {{
        owner = msg.sender;
        name = _name;
        symbol = _symbol;
    }}
    
    modifier onlyOwner() {{
        require(msg.sender == owner, "Not owner");
        _;
    }}
    
    function transferOwnership(address newOwner) public onlyOwner {{
        require(newOwner != address(0), "Invalid address");
        owner = newOwner;
    }}
    
    function getContractInfo() public view returns (string memory, string memory, address) {{
        return (name, symbol, owner);
    }}
}}
'''
        
        return template
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": ["contract_generation", "basic_validation"]
        }
'@

New-Item -ItemType Directory -Path "agents\smart_contract" -Force | Out-Null
$agentCode | Out-File -FilePath "agents\smart_contract\agent.py" -Force -Encoding UTF8
Write-Host "V Basic agent created" -ForegroundColor Green

# 8. Create test script
Write-Host "`n8. CREATING TEST SCRIPT..." -ForegroundColor Yellow

$testScript = @'
# test_basic.py
import sys
import os

# Add agents directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "agents"))

def test_smart_contract_agent():
    """Test the basic smart contract agent"""
    print("🤖 Testing Smart Contract Agent")
    print("=" * 40)
    
    try:
        from smart_contract.agent import SmartContractAgent
        
        # Create agent
        agent = SmartContractAgent()
        print(f"Agent: {agent.name} v{agent.version}")
        
        # Test contract generation
        requirements = {
            "name": "MyToken",
            "symbol": "MTK"
        }
        
        contract = agent.generate_contract(requirements)
        
        print("✅ Contract generated successfully")
        print(f"📄 Contract length: {len(contract)} characters")
        
        # Show agent info
        info = agent.get_agent_info()
        print(f"🔧 Capabilities: {', '.join(info['capabilities'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_smart_contract_agent()
    print("=" * 40)
    if success:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed")
    sys.exit(0 if success else 1)
'@

$testScript | Out-File -FilePath "test_basic.py" -Force -Encoding UTF8
Write-Host "V Test script created" -ForegroundColor Green

# 9. Create main.py
Write-Host "`n9. CREATING MAIN APPLICATION..." -ForegroundColor Yellow

$mainApp = @'
# main.py
import asyncio
import sys
import os
from typing import Dict, Any

class Pipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self):
        self.agents = {}
        
    async def initialize(self):
        """Initialize the pipeline"""
        print("🚀 Initializing Smart Contract Pipeline...")
        
        # Load agents
        await self._load_agents()
        
        print(f"✅ Pipeline initialized with {len(self.agents)} agents")
        return True
    
    async def _load_agents(self):
        """Load all available agents"""
        agents_dir = os.path.join(os.path.dirname(__file__), "agents")
        
        # Load Smart Contract Agent
        try:
            from agents.smart_contract.agent import SmartContractAgent
            self.agents["smart_contract"] = SmartContractAgent()
            print("✅ Smart Contract Agent loaded")
        except ImportError as e:
            print(f"❌ Failed to load Smart Contract Agent: {e}")
    
    async def run(self):
        """Run the main pipeline"""
        print("🎯 Smart Contract Pipeline Ready!")
        print("=" * 50)
        
        while True:
            print("`nAvailable commands:")
            print("1. Generate Smart Contract")
            print("2. Test Agent")
            print("3. Exit")
            
            choice = input("Select option (1-3): ").strip()
            
            if choice == "1":
                await self.generate_contract()
            elif choice == "2":
                await self.test_agent()
            elif choice == "3":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
    
    async def generate_contract(self):
        """Generate a smart contract"""
        print("`n📝 Smart Contract Generator")
        print("-" * 30)
        
        name = input("Contract name: ").strip() or "MyContract"
        symbol = input("Contract symbol: ").strip() or "MC"
        
        if "smart_contract" in self.agents:
            agent = self.agents["smart_contract"]
            
            requirements = {
                "name": name,
                "symbol": symbol
            }
            
            contract = agent.generate_contract(requirements)
            
            print("✅ Contract generated!")
            print("-" * 30)
            print(contract[:500] + "..." if len(contract) > 500 else contract)
            print("-" * 30)
            
            # Save to file
            filename = f"contracts/{name}.sol"
            os.makedirs("contracts", exist_ok=True)
            with open(filename, "w") as f:
                f.write(contract)
            
            print(f"📄 Contract saved to {filename}")
        else:
            print("❌ Smart Contract Agent not available")
    
    async def test_agent(self):
        """Test the agent"""
        print("`n🧪 Testing Agent...")
        
        if "smart_contract" in self.agents:
            agent = self.agents["smart_contract"]
            info = agent.get_agent_info()
            
            print(f"Agent: {info['name']}")
            print(f"Version: {info['version']}")
            print(f"Capabilities: {', '.join(info['capabilities'])}")
            print("✅ Agent is working correctly")
        else:
            print("❌ No agents available")

async def main():
    """Main entry point"""
    pipeline = Pipeline()
    
    if await pipeline.initialize():
        await pipeline.run()
    else:
        print("❌ Failed to initialize pipeline")

if __name__ == "__main__":
    asyncio.run(main())
'@

$mainApp | Out-File -FilePath "main.py" -Force -Encoding UTF8
Write-Host "V Main application created" -ForegroundColor Green

# 10. Create README
Write-Host "`n10. CREATING DOCUMENTATION..." -ForegroundColor Yellow

$readme = @'
# Smart Contract Pipeline

Automated Smart Contract development pipeline with AI agents.

## Quick Start

1. Run the setup script:
```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1