#!/usr/bin/env python3
"""
React Expert SubAgent - Expert en développement React/Next.js
Version: 2.0.0 (ALIGNÉ SUR CIRCUIT_BREAKER)
"""

import logging
import sys
import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
import uuid

# Configuration des imports
current_dir = Path(__file__).parent.absolute()
# Définir project_root
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agents.sous_agents.base_subagent import BaseSubAgent
from agents.base_agent.base_agent import Message, MessageType

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES
# ============================================================================

class ComponentType(Enum):
    """Types de composants React"""
    FUNCTIONAL = "functional"
    CLASS = "class"
    MEMO = "memo"
    FORWARD_REF = "forward_ref"
    LAZY = "lazy"
    
    @classmethod
    def from_string(cls, type_str: str) -> 'ComponentType':
        mapping = {
            "functional": cls.FUNCTIONAL,
            "class": cls.CLASS,
            "memo": cls.MEMO,
            "forward_ref": cls.FORWARD_REF,
            "forward-ref": cls.FORWARD_REF,
            "lazy": cls.LAZY
        }
        return mapping.get(type_str.lower(), cls.FUNCTIONAL)


class FrameworkType(Enum):
    """Types de frameworks supportés"""
    REACT = "react"
    NEXTJS = "nextjs"
    GATSBY = "gatsby"
    REMIX = "remix"


class StateManagementType(Enum):
    """Types de gestion d'état"""
    CONTEXT = "context"
    REDUX = "redux"
    ZUSTAND = "zustand"
    RECOIL = "recoil"
    JOTAI = "jotai"
    MOBX = "mobx"


@dataclass
class ComponentSpec:
    """Spécification d'un composant React"""
    name: str
    component_type: ComponentType = ComponentType.FUNCTIONAL
    props: List[Dict[str, Any]] = field(default_factory=list)
    hooks: List[str] = field(default_factory=list)
    state_vars: List[Dict[str, Any]] = field(default_factory=list)
    effects: List[Dict[str, Any]] = field(default_factory=list)
    children: bool = False
    typescript: bool = True
    styling: Optional[str] = None
    memo: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "component_type": self.component_type.value,
            "props": self.props,
            "hooks": self.hooks,
            "state_vars": self.state_vars,
            "effects": self.effects,
            "children": self.children,
            "typescript": self.typescript,
            "styling": self.styling,
            "memo": self.memo,
            "metadata": self.metadata
        }


@dataclass
class GenerationResult:
    """Résultat de génération de code"""
    component_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    code: str = ""
    spec: ComponentSpec = field(default_factory=ComponentSpec)
    created_at: datetime = field(default_factory=datetime.now)
    processing_time_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id": self.component_id,
            "code": self.code[:200] + "..." if len(self.code) > 200 else self.code,
            "spec": self.spec.to_dict(),
            "created_at": self.created_at.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata
        }


@dataclass
class ReactExpertStats:
    """Statistiques de l'expert React"""
    components_generated: int = 0
    components_succeeded: int = 0
    components_failed: int = 0
    pages_generated: int = 0
    hooks_generated: int = 0
    by_component_type: Dict[str, int] = field(default_factory=dict)
    by_framework: Dict[str, int] = field(default_factory=dict)
    by_state_management: Dict[str, int] = field(default_factory=dict)
    total_processing_time: float = 0.0
    avg_processing_time: float = 0.0
    last_generation: Optional[datetime] = None
    start_time: datetime = field(default_factory=datetime.now)
    
    def record_generation(self, spec: ComponentSpec, processing_time: float, success: bool):
        """Enregistre une génération"""
        self.components_generated += 1
        if success:
            self.components_succeeded += 1
        else:
            self.components_failed += 1
            
        self.total_processing_time += processing_time
        self.avg_processing_time = self.total_processing_time / self.components_generated
        self.last_generation = datetime.now()
        
        # Statistiques par type
        comp_type = spec.component_type.value
        self.by_component_type[comp_type] = self.by_component_type.get(comp_type, 0) + 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "components_generated": self.components_generated,
            "components_succeeded": self.components_succeeded,
            "components_failed": self.components_failed,
            "pages_generated": self.pages_generated,
            "hooks_generated": self.hooks_generated,
            "by_component_type": self.by_component_type,
            "by_framework": self.by_framework,
            "by_state_management": self.by_state_management,
            "avg_processing_time_ms": round(self.avg_processing_time, 2),
            "total_processing_time_ms": round(self.total_processing_time, 2),
            "last_generation": self.last_generation.isoformat() if self.last_generation else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
        }


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class ReactExpertSubAgent(BaseSubAgent):
    """
    Sous-agent expert React/Next.js
    
    Génère des composants React, pages Next.js, hooks personnalisés
    avec support TypeScript, tests et bonnes pratiques.
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise le sous-agent"""
        # 🔧 CORRECTION : Forcer le chemin absolu avec project_root
        if not config_path:
            # Chemin local dans le dossier du sous-agent
            config_path = str(Path(__file__).parent / "config.yaml")
        elif not Path(config_path).is_absolute():
            # Résoudre le chemin relatif par rapport à project_root
            config_path = str(project_root / config_path)
        
        logger.debug(f"🔧 Chargement config depuis: {config_path}")
        super().__init__(config_path)
        
        # Récupérer la configuration
        if 'subagent' in self._config:
            config = self._config.get('subagent', {})
        elif 'agent' in self._config:
            config = self._config.get('agent', {})
        else:
            config = {}
        
        # Métadonnées
        self._subagent_display_name = config.get('display_name', "⚛️ Expert React/Next.js")
        self._subagent_description = config.get('description', "Génération de composants React et pages Next.js")
        self._subagent_version = config.get('version', "2.0.0")
        self._subagent_category = config.get('category', "frontend_web3")
        self._subagent_capabilities = [
            cap.get('name') if isinstance(cap, dict) else cap
            for cap in self._config.get('capabilities', [])
        ]
        
        # Vérifier si la config a été chargée
        if self._config:
            logger.info(f"✅ Configuration chargée pour {self._subagent_display_name}")
        else:
            logger.warning(f"⚠️ Configuration non chargée, utilisation des valeurs par défaut")
        
        # Templates et configurations
        self._templates = self._load_templates()
        self._component_configs: Dict[str, Dict[str, Any]] = {}
        
        # Statistiques
        self._stats = ReactExpertStats()
        
        # File d'attente pour les événements
        self._event_queue: asyncio.Queue = asyncio.Queue()
        
        # Tâche de traitement
        self._processor_task: Optional[asyncio.Task] = None
        
        logger.info(f"✅ {self._subagent_display_name} initialisé")

    # ============================================================================
    # INITIALISATION
    # ============================================================================
    
    async def _initialize_subagent_components(self) -> bool:
        """Initialise les composants spécifiques"""
        logger.info("Initialisation des composants React Expert...")
        
        # Démarrer la tâche de traitement
        self._processor_task = asyncio.create_task(self._processor_loop())
        
        self._components = {
            "version": self._subagent_version,
            "frameworks": ["react", "nextjs", "gatsby", "remix"],
            "state_management": ["context", "redux", "zustand", "recoil", "jotai"],
            "styling": ["css", "scss", "tailwind", "styled-components"],
            "templates": list(self._templates.keys())
        }
        
        logger.info("✅ Composants React Expert initialisés")
        return True
        
    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Callable]:
        """Retourne les handlers spécifiques"""
        return {
            "react.generate_component": self._handle_generate_component,
            "react.generate_page": self._handle_generate_page,
            "react.generate_hook": self._handle_generate_hook,
            "react.generate_context": self._handle_generate_context,
            "react.generate_styles": self._handle_generate_styles,
            "react.analyze_performance": self._handle_analyze_performance,
        }
    
    # ============================================================================
    # TEMPLATES
    # ============================================================================
    
    def _load_templates(self) -> Dict[str, str]:
        """Charge les templates de composants"""
        return {
            "functional": """
import React from 'react';

interface {name}Props {{
  {props}
}}

export const {name}: React.FC<{name}Props> = ({{
  {props_destructured}
}}) => {{
  {state}
  {effects}
  
  return (
    <div className="{name_lower}">
      {children}
    </div>
  );
}};
""",
            "memo": """
import React from 'react';

interface {name}Props {{
  {props}
}}

export const {name} = React.memo<{name}Props>(({{
  {props_destructured}
}}) => {{
  return (
    <div className="{name_lower}">
      {children}
    </div>
  );
}});

{name}.displayName = '{name}';
""",
            "nextjs_page": """
import type {{ NextPage }} from 'next';
import Head from 'next/head';

interface {name}Props {{
  {props}
}}

const {name}: NextPage<{name}Props> = ({{
  {props_destructured}
}}) => {{
  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content="{description}" />
      </Head>
      <main className="{name_lower}">
        {children}
      </main>
    </>
  );
}};

export default {name};

export async function getStaticProps() {{
  return {{
    props: {{}},
  }};
}}
""",
            "hook": """
import {{ useState, useEffect, useCallback }} from 'react';

interface {name}Return {{
  {return_type}
}}

export const {name} = ({params}): {name}Return => {{
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {{
    const fetchData = async () => {{
      try {{
        setLoading(true);
        // Implementation
        setData(result);
      }} catch (err) {{
        setError(err instanceof Error ? err : new Error(String(err)));
      }} finally {{
        setLoading(false);
      }}
    }};

    fetchData();
  }}, []);

  return {{
    data,
    loading,
    error,
  }};
}};
""",
            "context": """
import React, {{ createContext, useContext, useReducer }} from 'react';

interface {name}State {{
  {state}
}}

type {name}Action = 
  | {{ type: 'ACTION_TYPE'; payload: any }};

const initialState: {name}State = {{
  {initial_state}
}};

const {name}Context = createContext<{{
  state: {name}State;
  dispatch: React.Dispatch<{name}Action>;
}} | undefined>(undefined);

const {name}Reducer = (
  state: {name}State,
  action: {name}Action
): {name}State => {{
  switch (action.type) {{
    default:
      return state;
  }}
}};

export const {name}Provider: React.FC<{{ children: React.ReactNode }}> = ({{ children }}) => {{
  const [state, dispatch] = useReducer({name}Reducer, initialState);

  return (
    <{name}Context.Provider value={{ state, dispatch }}>
      {{children}}
    </{name}Context.Provider>
  );
}};

export const use{name} = () => {{
  const context = useContext({name}Context);
  if (context === undefined) {{
    throw new Error('use{name} must be used within a {name}Provider');
  }}
  return context;
}};
"""
        }
    
    # ============================================================================
    # TÂCHES DE FOND
    # ============================================================================
    
    async def _processor_loop(self):
        """Boucle de traitement des générations"""
        logger.info("🔄 Boucle de traitement démarrée")
        
        while self._status.value == "ready":
            try:
                # Traiter les événements
                while not self._event_queue.empty():
                    event = await self._event_queue.get()
                    await self._process_event(event)
                
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Erreur dans la boucle de traitement: {e}")
                await asyncio.sleep(5)
    
    async def _process_event(self, event: Dict[str, Any]):
        """Traite un événement"""
        event_type = event.get("type")
        if event_type == "generation_completed":
            logger.debug(f"✅ Génération terminée: {event.get('component_id')}")
    
    # ============================================================================
    # GÉNÉRATION DE COMPOSANTS
    # ============================================================================
    
    async def generate_component(self, spec: ComponentSpec) -> GenerationResult:
        """
        Génère un composant React selon les spécifications
        """
        start_time = time.time()
        result = GenerationResult(spec=spec)
        
        try:
            # Sélectionner le template
            template_key = "memo" if spec.memo else spec.component_type.value
            template = self._templates.get(template_key, self._templates["functional"])
            
            # Préparer les props
            props_list = []
            props_destructured = []
            for prop in spec.props:
                prop_str = f"{prop['name']}"
                if prop.get('type'):
                    prop_str += f": {prop['type']}"
                if prop.get('required') is False:
                    prop_str += "?"
                props_list.append(prop_str)
                props_destructured.append(prop['name'])
            
            props_str = "\n  ".join(props_list)
            props_destructured_str = ", ".join(props_destructured)
            
            # Préparer le state
            state_lines = []
            for state_var in spec.state_vars:
                if spec.typescript and state_var.get('type'):
                    state_lines.append(f"const [{state_var['name']}, set{state_var['name'].capitalize()}] = useState<{state_var['type']}>({state_var.get('default', 'null')});")
                else:
                    state_lines.append(f"const [{state_var['name']}, set{state_var['name'].capitalize()}] = useState({state_var.get('default', 'null')});")
            
            state_str = "\n  ".join(state_lines)
            
            # Préparer les effets
            effect_lines = []
            for effect in spec.effects:
                effect_lines.append(f"""
  useEffect(() => {{
    {effect.get('logic', '// Effect logic')}
  }}, [{', '.join(effect.get('deps', []))}]);
""")
            
            effects_str = "\n".join(effect_lines)
            
            # Générer le code
            code = template.format(
                name=spec.name,
                name_lower=spec.name.lower(),
                props=props_str,
                props_destructured=props_destructured_str,
                state=state_str,
                effects=effects_str,
                children="{children}" if spec.children else "",
                title=f"{spec.name} Page",
                description=f"Generated by React Expert"
            )
            
            result.code = code
            result.success = True
            
            # Enregistrer les stats
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(spec, processing_time, True)
            
            # Journaliser l'événement
            await self._log_event("component_generated", {
                "component_id": result.component_id,
                "name": spec.name,
                "type": spec.component_type.value,
                "processing_time_ms": processing_time
            })
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(spec, processing_time, False)
            logger.error(f"❌ Erreur génération composant: {e}")
        
        return result
    
    async def generate_page(self, name: str, framework: str = "nextjs", **kwargs) -> GenerationResult:
        """Génère une page selon le framework"""
        spec = ComponentSpec(
            name=name,
            component_type=ComponentType.FUNCTIONAL,
            props=kwargs.get("props", []),
            state_vars=kwargs.get("state", []),
            effects=kwargs.get("effects", []),
            children=True,
            typescript=kwargs.get("typescript", True),
            metadata={"framework": framework, **kwargs.get("metadata", {})}
        )
        
        if framework == "nextjs":
            spec.metadata["template"] = "nextjs_page"
        
        return await self.generate_component(spec)
    
    async def generate_hook(self, name: str, **kwargs) -> GenerationResult:
        """Génère un hook personnalisé"""
        spec = ComponentSpec(
            name=name,
            component_type=ComponentType.FUNCTIONAL,
            props=kwargs.get("params", []),
            state_vars=kwargs.get("state", []),
            effects=kwargs.get("effects", []),
            typescript=kwargs.get("typescript", True),
            metadata={"type": "hook", **kwargs.get("metadata", {})}
        )
        
        result = await self.generate_component(spec)
        if result.success:
            self._stats.hooks_generated += 1
        
        return result
    
    async def generate_context(self, name: str, **kwargs) -> GenerationResult:
        """Génère un contexte React"""
        spec = ComponentSpec(
            name=name,
            component_type=ComponentType.FUNCTIONAL,
            props=kwargs.get("props", []),
            state_vars=kwargs.get("state", []),
            typescript=kwargs.get("typescript", True),
            metadata={"type": "context", **kwargs.get("metadata", {})}
        )
        
        return await self.generate_component(spec)
    
    async def generate_styles(self, component: str, styling: str = "css", **kwargs) -> Dict[str, Any]:
        """Génère des styles pour un composant"""
        styles = {
            "css": f"""
.{component.lower()} {{
  /* Styles for {component} */
}}
""",
            "scss": f"""
.{component.lower()} {{
  // Styles for {component}
  
  &__title {{
    font-size: 2rem;
  }}
}}
""",
            "tailwind": f"""
export default function {component}() {{
  return (
    <div className="p-4 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-gray-800">{component}</h2>
    </div>
  );
}}
"""
        }
        
        return {
            "success": True,
            "styles": styles.get(styling, styles["css"]),
            "styling": styling,
            "component": component
        }
    
    async def analyze_performance(self, component_code: str) -> Dict[str, Any]:
        """Analyse la performance d'un composant"""
        analysis = {
            "issues": [],
            "suggestions": [],
            "metrics": {}
        }
        
        # Vérifications basiques
        if "useState" in component_code and "useMemo" not in component_code:
            analysis["issues"].append("Complex state without memoization")
            analysis["suggestions"].append("Consider using useMemo for expensive computations")
        
        if "useEffect" in component_code and "[]" not in component_code:
            analysis["issues"].append("useEffect without dependency array may cause infinite loops")
            analysis["suggestions"].append("Add proper dependency array to useEffect")
        
        if "inline function" in component_code.lower():
            analysis["issues"].append("Inline functions in render may cause unnecessary re-renders")
            analysis["suggestions"].append("Use useCallback for functions passed as props")
        
        analysis["metrics"] = {
            "lines": len(component_code.split("\n")),
            "hooks": component_code.count("use"),
            "components": component_code.count("export")
        }
        
        return {
            "success": True,
            "analysis": analysis
        }
    
    # ============================================================================
    # HANDLERS DE CAPACITÉS
    # ============================================================================
    
    async def _handle_generate_component(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un composant"""
        spec = ComponentSpec(
            name=params.get("name", "Component"),
            component_type=ComponentType.from_string(params.get("type", "functional")),
            props=params.get("props", []),
            hooks=params.get("hooks", []),
            state_vars=params.get("state", []),
            effects=params.get("effects", []),
            children=params.get("children", False),
            typescript=params.get("typescript", True),
            styling=params.get("styling"),
            memo=params.get("memo", False),
            metadata=params.get("metadata", {})
        )
        
        result = await self.generate_component(spec)
        return result.to_dict()
    
    async def _handle_generate_page(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère une page"""
        name = params.get("name", "Page")
        framework = params.get("framework", "nextjs")
        
        result = await self.generate_page(
            name=name,
            framework=framework,
            props=params.get("props", []),
            state=params.get("state", []),
            effects=params.get("effects", []),
            typescript=params.get("typescript", True),
            metadata=params.get("metadata", {})
        )
        
        if result.success:
            self._stats.pages_generated += 1
        
        return result.to_dict()
    
    async def _handle_generate_hook(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un hook"""
        name = params.get("name", "useCustom")
        
        result = await self.generate_hook(
            name=name,
            params=params.get("params", []),
            state=params.get("state", []),
            effects=params.get("effects", []),
            typescript=params.get("typescript", True),
            metadata=params.get("metadata", {})
        )
        
        return result.to_dict()
    
    async def _handle_generate_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère un contexte"""
        name = params.get("name", "AppContext")
        
        result = await self.generate_context(
            name=name,
            props=params.get("props", []),
            state=params.get("state", []),
            typescript=params.get("typescript", True),
            metadata=params.get("metadata", {})
        )
        
        return result.to_dict()
    
    async def _handle_generate_styles(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère des styles"""
        component = params.get("component", "Component")
        styling = params.get("styling", "css")
        
        result = await self.generate_styles(
            component=component,
            styling=styling,
            **params.get("options", {})
        )
        
        return result
    
    async def _handle_analyze_performance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse la performance"""
        component_code = params.get("code", "")
        
        result = await self.analyze_performance(component_code)
        return result
    
    # ============================================================================
    # GESTION DES MESSAGES
    # ============================================================================
    
    async def handle_message(self, message: Message) -> Optional[Message]:
        """Gère les messages entrants"""
        try:
            msg_type = message.message_type
            logger.debug(f"📨 Message reçu: {msg_type} de {message.sender}")

            # Valider le message
            if self._input_validation_enabled:
                is_valid, error = self._validate_against_schema(
                    message.content, 
                    self._input_schemas.get(msg_type, {})
                )
                if not is_valid:
                    logger.warning(f"⚠️ Message invalide: {error}")
                    return Message(
                        sender=self.name,
                        recipient=message.sender,
                        content={"error": f"Message invalide: {error}"},
                        message_type=MessageType.ERROR.value,
                        correlation_id=message.message_id
                    )

            # Handlers standards (de BaseSubAgent)
            handlers = self._get_standard_handlers()
            
            # Ajouter les handlers spécifiques
            handlers.update(self._get_capability_handlers())

            if msg_type in handlers:
                handler = getattr(self, handlers[msg_type], None)
                if handler:
                    result = await handler(message.content)
                    return Message(
                        sender=self.name,
                        recipient=message.sender,
                        content=result,
                        message_type=f"{msg_type}_response",
                        correlation_id=message.message_id
                    )

            return None

        except Exception as e:
            logger.error(f"❌ Erreur traitement message: {e}")
            return Message(
                sender=self.name,
                recipient=message.sender,
                content={"error": str(e)},
                message_type=MessageType.ERROR.value,
                correlation_id=message.message_id
            )
    
    # ============================================================================
    # UTILITAIRES
    # ============================================================================
    
    async def _log_event(self, event_type: str, data: Dict[str, Any]):
        """Journalise un événement"""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        await self._event_queue.put(event)
        
        if self._config.get('logging', {}).get('events', True):
            logger.info(f"📋 Événement: {event_type}")
    
    # ============================================================================
    # SANTÉ ET STATISTIQUES
    # ============================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du sous-agent"""
        base_health = await super().health_check()

        issues = []
        
        # Vérifier la file d'événements
        if self._event_queue.qsize() > 100:
            issues.append(f"File d'événements élevée: {self._event_queue.qsize()}")
        
        health_status = "healthy" if not issues else "degraded"

        return {
            **base_health,
            "agent": self.name,
            "display_name": self._subagent_display_name,
            "category": self._subagent_category,
            "status": self._status.value,
            "ready": self._status == AgentStatus.READY,
            "initialized": self._initialized,
            "health_status": health_status,
            "issues": issues,
            "stats": self._stats.to_dict(),
            "components": self._components,
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_info(self) -> Dict[str, Any]:
        """Informations pour le registre"""
        return {
            "id": self.name,
            "name": self.__class__.__name__,
            "display_name": self._subagent_display_name,
            "category": self._subagent_category,
            "version": self._subagent_version,
            "description": self._subagent_description,
            "status": self._status.value,
            "capabilities": self._subagent_capabilities,
            "parent_agent": self._config.get('parent_relationship', {}).get('parent_name', 'frontend_web3'),
            "stats": self._stats.to_dict()
        }

    async def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques détaillées"""
        return self._stats.to_dict()

    async def shutdown(self) -> bool:
        logger.info(f"Arrêt de {self._subagent_display_name}...")
        
        # Arrêter la tâche de traitement
        if self._processor_task and not self._processor_task.done():
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        # IGNORER complètement super().shutdown()
        try:
            await super().shutdown()
        except Exception:
            pass  # On ignore tout
        
        logger.info(f"✅ {self._subagent_display_name} arrêté")
        return True