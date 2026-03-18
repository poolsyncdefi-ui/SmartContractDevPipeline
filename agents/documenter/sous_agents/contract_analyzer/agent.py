#!/usr/bin/env python3
"""
ContractAnalyzer SubAgent - Analyseur de contrats Solidity
Version: 2.2.0 (ALIGNÉ SUR COMMUNICATION)
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import time

project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent
from agents.base_agent.base_agent import Message, MessageType


class ContractAnalyzerSubAgent(BaseSubAgent):
    """
    Sous-agent spécialisé dans l'analyse de contrats Solidity
    Version 2.2 - Aligné sur l'architecture Communication
    """

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        
        subagent_config = self._config.get('subagent', {})
        self._display_name = subagent_config.get('display_name', '🔍 Analyseur de Contrats')
        
        self._initialized = False
        self._contracts_analyzed = 0
        self._contracts_failed = 0
        
        self._stats = {
            "contracts_analyzed": 0,
            "contracts_failed": 0,
            "functions_extracted": 0,
            "events_extracted": 0,
            "modifiers_extracted": 0,
            "processing_time_total": 0,
            "processing_time_avg": 0,
            "uptime_start": datetime.now().isoformat()
        }
        
        self._logger.info(f"{self._display_name} créé")

    async def _initialize_subagent_components(self) -> bool:
        try:
            self._components = {
                "version": "2.2.0",
                "supports_solidity": True,
                "supports_vyper": False,
                "supports_natspec": True,
                "max_file_size_kb": 1024
            }
            return True
        except Exception as e:
            self._logger.error(f"Erreur composants: {e}")
            return False

    async def _initialize_components(self) -> bool:
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, str]:
        return {
            "analyze_contract": "handle_analyze_contract",
            "extract_functions": "handle_extract_functions",
            "extract_events": "handle_extract_events",
            "extract_modifiers": "handle_extract_modifiers",
            "extract_abi": "handle_extract_abi",
            "parse_natspec": "handle_parse_natspec",
            "validate_syntax": "handle_validate_syntax"
        }

    def _get_features(self) -> Dict[str, Any]:
        return {
            "languages": ["solidity"],
            "natspec_tags": ["@param", "@return", "@dev", "@notice", "@title", "@author"],
            "extractable": ["functions", "events", "modifiers", "variables", "structs", "enums"],
            "max_file_size_kb": 1024
        }

    async def analyze_contract(self, contract_path: str) -> Dict[str, Any]:
        """Analyse un contrat Solidity complet"""
        start_time = time.time()
        
        try:
            if not os.path.exists(contract_path):
                return {"success": False, "error": f"Fichier non trouvé: {contract_path}"}
            
            with open(contract_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extraction des différentes parties
            functions = await self._extract_functions(content)
            events = await self._extract_events(content)
            modifiers = await self._extract_modifiers(content)
            variables = await self._extract_state_variables(content)
            structs = await self._extract_structs(content)
            enums = await self._extract_enums(content)
            natspec = await self._parse_natspec(content)
            
            # Métadonnées du contrat
            contract_name = self._extract_contract_name(content)
            license_info = self._extract_license(content)
            pragma = self._extract_pragma(content)
            inheritance = self._extract_inheritance(content)
            dependencies = self._extract_imports(content)
            
            processing_time = time.time() - start_time
            self._contracts_analyzed += 1
            self._stats["contracts_analyzed"] += 1
            self._stats["functions_extracted"] += len(functions)
            self._stats["events_extracted"] += len(events)
            self._stats["modifiers_extracted"] += len(modifiers)
            self._stats["processing_time_total"] += processing_time
            self._stats["processing_time_avg"] = self._stats["processing_time_total"] / self._stats["contracts_analyzed"]
            
            return {
                "success": True,
                "name": contract_name,
                "license": license_info,
                "pragma": pragma,
                "inheritance": inheritance,
                "dependencies": dependencies,
                "functions": functions,
                "events": events,
                "modifiers": modifiers,
                "state_variables": variables,
                "structs": structs,
                "enums": enums,
                "natspec": natspec,
                "stats": {
                    "functions": len(functions),
                    "events": len(events),
                    "modifiers": len(modifiers),
                    "variables": len(variables),
                    "structs": len(structs),
                    "enums": len(enums)
                },
                "file_size": len(content),
                "processing_time": processing_time
            }
            
        except Exception as e:
            self._contracts_failed += 1
            self._stats["contracts_failed"] += 1
            return {"success": False, "error": str(e)}

    def _extract_contract_name(self, content: str) -> str:
        """Extrait le nom du contrat"""
        match = re.search(r'contract\s+(\w+)', content)
        return match.group(1) if match else "Unknown"

    def _extract_license(self, content: str) -> str:
        """Extrait la licence SPDX"""
        match = re.search(r'SPDX-License-Identifier:\s*(\S+)', content)
        return match.group(1) if match else "UNLICENSED"

    def _extract_pragma(self, content: str) -> str:
        """Extrait la version pragma"""
        match = re.search(r'pragma\s+solidity\s+([^;]+);', content)
        return match.group(1) if match else "unknown"

    def _extract_inheritance(self, content: str) -> List[str]:
        """Extrait les parents hérités"""
        match = re.search(r'contract\s+\w+\s+is\s+([^{]+)', content)
        if match:
            parents = match.group(1).strip()
            return [p.strip() for p in parents.split(',') if p.strip()]
        return []

    def _extract_imports(self, content: str) -> List[str]:
        """Extrait les imports/dépendances"""
        imports = re.findall(r'import\s+["\']([^"\']+)["\']', content)
        return list(set(imports))

    async def _extract_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extrait les fonctions du contrat"""
        functions = []
        
        # Pattern pour les fonctions
        func_pattern = r'function\s+(\w+)\s*\(([^)]*)\)\s*(public|private|internal|external)?\s*(view|pure|payable)?\s*(returns?\s*\(([^)]*)\))?\s*{'
        
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            name = match.group(1)
            params_str = match.group(2)
            visibility = match.group(3) or 'public'
            mutability = match.group(4) or 'nonpayable'
            returns = match.group(6) or ''
            
            # Parser les paramètres
            params = []
            if params_str.strip():
                for param in params_str.split(','):
                    param = param.strip()
                    if param:
                        parts = param.split()
                        if len(parts) >= 2:
                            param_type = parts[0]
                            param_name = parts[1] if len(parts) > 1 else ''
                            params.append({
                                "type": param_type,
                                "name": param_name
                            })
            
            functions.append({
                "name": name,
                "params": params,
                "visibility": visibility,
                "mutability": mutability,
                "returns": returns.strip(),
                "signature": f"{name}({','.join([p['type'] for p in params])})"
            })
        
        return functions

    async def _extract_events(self, content: str) -> List[Dict[str, Any]]:
        """Extrait les événements du contrat"""
        events = []
        
        pattern = r'event\s+(\w+)\s*\(([^)]*)\)'
        
        for match in re.finditer(pattern, content):
            name = match.group(1)
            params_str = match.group(2)
            
            params = []
            if params_str.strip():
                for param in params_str.split(','):
                    param = param.strip()
                    if param:
                        parts = param.split()
                        if len(parts) >= 2:
                            param_type = parts[0]
                            param_name = parts[1] if len(parts) > 1 else ''
                            indexed = 'indexed' in param
                            params.append({
                                "type": param_type,
                                "name": param_name,
                                "indexed": indexed
                            })
            
            events.append({
                "name": name,
                "params": params
            })
        
        return events

    async def _extract_modifiers(self, content: str) -> List[Dict[str, Any]]:
        """Extrait les modifiers du contrat"""
        modifiers = []
        
        pattern = r'modifier\s+(\w+)\s*\(([^)]*)\)\s*{'
        
        for match in re.finditer(pattern, content):
            name = match.group(1)
            params_str = match.group(2)
            
            params = []
            if params_str.strip():
                for param in params_str.split(','):
                    param = param.strip()
                    if param:
                        parts = param.split()
                        if len(parts) >= 2:
                            param_type = parts[0]
                            param_name = parts[1]
                            params.append({
                                "type": param_type,
                                "name": param_name
                            })
            
            modifiers.append({
                "name": name,
                "params": params
            })
        
        return modifiers

    async def _extract_state_variables(self, content: str) -> List[Dict[str, Any]]:
        """Extrait les variables d'état"""
        variables = []
        
        pattern = r'(?:public|private|internal)?\s+(\w+)\s+(public|private|internal)?\s+(\w+)\s*;'
        
        for match in re.finditer(pattern, content):
            var_type = match.group(1)
            visibility = match.group(2) or 'internal'
            name = match.group(3)
            
            variables.append({
                "type": var_type,
                "name": name,
                "visibility": visibility
            })
        
        return variables

    async def _extract_structs(self, content: str) -> List[Dict[str, Any]]:
        """Extrait les structs"""
        structs = []
        
        pattern = r'struct\s+(\w+)\s*{([^}]+)}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            name = match.group(1)
            fields_str = match.group(2)
            
            fields = []
            for line in fields_str.split(';'):
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        field_type = parts[0]
                        field_name = parts[1]
                        fields.append({
                            "type": field_type,
                            "name": field_name
                        })
            
            structs.append({
                "name": name,
                "fields": fields
            })
        
        return structs

    async def _extract_enums(self, content: str) -> List[Dict[str, Any]]:
        """Extrait les enums"""
        enums = []
        
        pattern = r'enum\s+(\w+)\s*{([^}]+)}'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            name = match.group(1)
            values_str = match.group(2)
            
            values = [v.strip() for v in values_str.split(',') if v.strip()]
            
            enums.append({
                "name": name,
                "values": values
            })
        
        return enums

    async def _parse_natspec(self, content: str) -> Dict[str, Any]:
        """Parse les commentaires NatSpec"""
        natspec = {
            "contract": {},
            "functions": {},
            "events": {},
            "modifiers": {}
        }
        
        # Pattern pour les commentaires NatSpec
        pattern = r'/\*\*\s*(.*?)\s*\*/'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            comment = match.group(1)
            lines = comment.split('\n')
            
            current_item = None
            current_tags = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('*'):
                    line = line[1:].strip()
                
                # Détecter le type d'élément documenté
                if '@title' in line:
                    natspec["contract"]["title"] = line.replace('@title', '').strip()
                elif '@author' in line:
                    natspec["contract"]["author"] = line.replace('@author', '').strip()
                elif '@notice' in line:
                    natspec["contract"]["notice"] = line.replace('@notice', '').strip()
                elif '@dev' in line:
                    natspec["contract"]["dev"] = line.replace('@dev', '').strip()
                elif '@param' in line:
                    param_match = re.search(r'@param\s+(\w+)\s+(.+)', line)
                    if param_match:
                        if 'params' not in current_tags:
                            current_tags['params'] = []
                        current_tags['params'].append({
                            "name": param_match.group(1),
                            "description": param_match.group(2)
                        })
                elif '@return' in line:
                    current_tags['return'] = line.replace('@return', '').strip()
        
        return natspec

    async def extract_abi(self, contract_info: Dict[str, Any]) -> Dict[str, Any]:
        """Génère l'ABI à partir des informations du contrat"""
        abi = []
        
        # Fonctions
        for func in contract_info.get("functions", []):
            abi_item = {
                "type": "function",
                "name": func["name"],
                "inputs": [
                    {"name": p.get("name", ""), "type": p["type"]}
                    for p in func.get("params", [])
                ],
                "outputs": [],
                "stateMutability": func.get("mutability", "nonpayable")
            }
            
            if func.get("returns"):
                abi_item["outputs"].append({
                    "name": "",
                    "type": func["returns"]
                })
            
            abi.append(abi_item)
        
        # Événements
        for event in contract_info.get("events", []):
            abi.append({
                "type": "event",
                "name": event["name"],
                "inputs": [
                    {
                        "name": p.get("name", ""),
                        "type": p["type"],
                        "indexed": p.get("indexed", False)
                    }
                    for p in event.get("params", [])
                ],
                "anonymous": False
            })
        
        return {
            "success": True,
            "abi": abi,
            "functions": len([i for i in abi if i["type"] == "function"]),
            "events": len([i for i in abi if i["type"] == "event"])
        }

    async def validate_syntax(self, content: str) -> Dict[str, Any]:
        """Valide la syntaxe de base du contrat"""
        issues = []
        
        # Vérifications basiques
        if not content.strip():
            issues.append("Fichier vide")
        
        if "contract" not in content:
            issues.append("Aucun contrat trouvé")
        
        if "pragma solidity" not in content:
            issues.append("Pragma solidity manquant")
        
        # Vérifier les parenthèses et accolades
        if content.count('{') != content.count('}'):
            issues.append("Accolades non équilibrées")
        
        if content.count('(') != content.count(')'):
            issues.append("Parenthèses non équilibrées")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "line_count": len(content.split('\n'))
        }

    async def handle_analyze_contract(self, message: Message) -> Message:
        content = message.content
        result = await self.analyze_contract(content.get("path"))
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="contract_analyzed",
            correlation_id=message.message_id
        )

    async def handle_extract_functions(self, message: Message) -> Message:
        content = message.content
        functions = await self._extract_functions(content.get("source", ""))
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content={"success": True, "functions": functions, "count": len(functions)},
            message_type="functions_extracted",
            correlation_id=message.message_id
        )

    async def handle_extract_events(self, message: Message) -> Message:
        content = message.content
        events = await self._extract_events(content.get("source", ""))
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content={"success": True, "events": events, "count": len(events)},
            message_type="events_extracted",
            correlation_id=message.message_id
        )

    async def handle_extract_modifiers(self, message: Message) -> Message:
        content = message.content
        modifiers = await self._extract_modifiers(content.get("source", ""))
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content={"success": True, "modifiers": modifiers, "count": len(modifiers)},
            message_type="modifiers_extracted",
            correlation_id=message.message_id
        )

    async def handle_extract_abi(self, message: Message) -> Message:
        result = await self.extract_abi(message.content.get("contract_info", {}))
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="abi_extracted",
            correlation_id=message.message_id
        )

    async def handle_parse_natspec(self, message: Message) -> Message:
        result = await self._parse_natspec(message.content.get("source", ""))
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content={"success": True, "natspec": result},
            message_type="natspec_parsed",
            correlation_id=message.message_id
        )

    async def handle_validate_syntax(self, message: Message) -> Message:
        result = await self.validate_syntax(message.content.get("source", ""))
        return Message(
            sender=self.__class__.__name__,
            recipient=message.sender,
            content=result,
            message_type="syntax_validated",
            correlation_id=message.message_id
        )

    async def handle_message(self, message: Message) -> Optional[Message]:
        try:
            msg_type = message.message_type
            handlers = self._get_capability_handlers()
            
            if msg_type in handlers:
                handler = getattr(self, handlers[msg_type], None)
                if handler:
                    return await handler(message)
            
            return Message(
                sender=self.__class__.__name__,
                recipient=message.sender,
                content={"error": f"Type non supporté: {msg_type}"},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )
        except Exception as e:
            return Message(
                sender=self.__class__.__name__,
                recipient=message.sender,
                content={"error": str(e)},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )

    async def health_check(self) -> Dict[str, Any]:
        uptime = None
        if self._stats.get('uptime_start'):
            start = datetime.fromisoformat(self._stats['uptime_start'])
            uptime = str(datetime.now() - start)

        success_rate = 0
        total = self._stats["contracts_analyzed"] + self._stats["contracts_failed"]
        if total > 0:
            success_rate = (self._stats["contracts_analyzed"] / total) * 100

        return {
            "status": self._status,
            "ready": self._initialized,
            "display_name": self._display_name,
            "uptime": uptime,
            "stats": {
                "contracts_analyzed": self._stats["contracts_analyzed"],
                "contracts_failed": self._stats["contracts_failed"],
                "functions_extracted": self._stats["functions_extracted"],
                "events_extracted": self._stats["events_extracted"],
                "modifiers_extracted": self._stats["modifiers_extracted"],
                "success_rate": round(success_rate, 2),
                "processing_time_avg": round(self._stats["processing_time_avg"], 3)
            },
            "components": self._components,
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        return {
            "id": "ContractAnalyzerSubAgent",
            "name": self._display_name,
            "version": "2.2.0",
            "status": self._status,
            "capabilities": list(self._get_capability_handlers().keys()),
            "features": self._get_features(),
            "stats": {
                "contracts_analyzed": self._stats["contracts_analyzed"],
                "functions_extracted": self._stats["functions_extracted"],
                "success_rate": round(
                    (self._stats["contracts_analyzed"] / max(1, self._stats["contracts_analyzed"] + self._stats["contracts_failed"])) * 100, 2
                )
            }
        }

    async def get_stats(self) -> Dict[str, Any]:
        return self._stats

    async def shutdown(self) -> bool:
        self._logger.info(f"Arrêt de {self._display_name}...")
        await self._save_stats()
        
        # Appeler super().shutdown() mais ignorer son retour
        try:
            await super().shutdown()
        except Exception:
            pass  # Ignorer toute erreur
        
        return True

    async def _save_stats(self):
        try:
            stats_file = Path("./reports") / "documenter" / "contract_analyzer" / f"stats_{datetime.now().strftime('%Y%m%d')}.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self._stats, f, indent=2, default=str)
        except Exception as e:
            self._logger.warning(f"Impossible de sauvegarder: {e}")