# workflow/fullstack_integration.py
class FullStackIntegration:
    """Intègre smart contracts et frontend de manière cohérente"""
    
    async def integrate(self, smart_contracts: dict, frontend_specs: dict):
        """Intègre les deux parties"""
        
        # 1. Génération des types TypeScript depuis les ABI
        types = await self._generate_typescript_types(smart_contracts["abi"])
        
        # 2. Création des hooks React personnalisés
        hooks = await self._generate_web3_hooks(smart_contracts, types)
        
        # 3. Génération des composants UI
        components = await self._generate_ui_components(
            frontend_specs, 
            hooks
        )
        
        # 4. Création des pages
        pages = await self._generate_pages(components, hooks)
        
        # 5. Configuration de l'application
        app_config = await self._generate_app_config(smart_contracts)
        
        # 6. Tests d'intégration
        integration_tests = await self._generate_integration_tests(
            smart_contracts, 
            components
        )
        
        return {
            "types": types,
            "hooks": hooks,
            "components": components,
            "pages": pages,
            "config": app_config,
            "tests": integration_tests
        }
    
    async def _generate_typescript_types(self, abi: list):
        """Génère les types TypeScript depuis l'ABI"""
        from web3_type_generator import generate_types
        
        types = generate_types(abi, {
            "output_dir": "types/",
            "flatten": True,
            "use_web3_types": True
        })
        
        # Ajout de types utilitaires
        utility_types = """
        export type TransactionStatus = 
          | 'pending' 
          | 'success' 
          | 'error' 
          | 'reverted';
        
        export type NetworkConfig = {
          chainId: number;
          name: string;
          rpcUrl: string;
          explorerUrl: string;
        };
        """
        
        return types + utility_types
    
    async def _generate_web3_hooks(self, contracts: dict, types: str):
        """Génère des hooks React pour interagir avec les contrats"""
        hooks = []
        
        for contract_name, contract_data in contracts.items():
            # Hook pour lire l'état
            read_hook = f"""
            export const use{contract_name} = () => {{
              const {{ config }} = useNetwork();
              const {{ address }} = useAccount();
              
              const contract = useContract({{
                address: {contract_data.address},
                abi: {contract_data.abi},
              }});
              
              // Exemple: Lecture d'un état
              const useBalance = () => {{
                return useContractRead({{
                  address: contract.address,
                  abi: contract.abi,
                  functionName: 'balanceOf',
                  args: [address],
                  watch: true,
                }});
              }};
              
              // Exemple: Écriture
              const useTransfer = () => {{
                const {{ write, isLoading, error }} = useContractWrite({{
                  address: contract.address,
                  abi: contract.abi,
                  functionName: 'transfer',
                  mode: 'recklesslyUnprepared',
                }});
                
                return {{ transfer: write, isLoading, error }};
              }};
              
              return {{ useBalance, useTransfer }};
            }};
            """
            hooks.append(read_hook)
        
        return hooks