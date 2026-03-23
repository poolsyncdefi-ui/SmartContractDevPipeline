#!/usr/bin/env python3
"""
UiUxExpert SubAgent - Expert UI/UX Design
Version: 2.0.0 (ALIGNÉ SUR CIRCUIT_BREAKER)

Expert en design system, composants accessibles, animations fluides,
responsive design et dark mode.
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
from agents.base_agent.base_agent import Message, MessageType, AgentStatus

logger = logging.getLogger(__name__)


# ============================================================================
# ÉNUMS ET CLASSES DE DONNÉES
# ============================================================================

class DesignSystemType(Enum):
    """Types de systèmes de design"""
    MATERIAL = "material"
    TAILWIND = "tailwind"
    CHAKRA = "chakra"
    RADIX = "radix"
    CUSTOM = "custom"
    
    @classmethod
    def from_string(cls, type_str: str) -> 'DesignSystemType':
        mapping = {
            "material": cls.MATERIAL,
            "tailwind": cls.TAILWIND,
            "chakra": cls.CHAKRA,
            "radix": cls.RADIX,
            "custom": cls.CUSTOM
        }
        return mapping.get(type_str.lower(), cls.CUSTOM)


class ColorMode(Enum):
    """Modes de couleur"""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"
    AUTO = "auto"


class AccessibilityLevel(Enum):
    """Niveaux d'accessibilité"""
    WCAG_A = "A"
    WCAG_AA = "AA"
    WCAG_AAA = "AAA"
    
    @classmethod
    def from_string(cls, level_str: str) -> 'AccessibilityLevel':
        mapping = {
            "A": cls.WCAG_A,
            "AA": cls.WCAG_AA,
            "AAA": cls.WCAG_AAA
        }
        return mapping.get(level_str.upper(), cls.WCAG_AA)


@dataclass
class ColorPalette:
    """Palette de couleurs"""
    primary: str = "#00ff88"
    secondary: str = "#8b5cf6"
    accent: str = "#3b82f6"
    background: str = "#ffffff"
    surface: str = "#f8f9fa"
    text: str = "#1a1e24"
    text_secondary: str = "#6c757d"
    success: str = "#10b981"
    warning: str = "#f59e0b"
    error: str = "#ef4444"
    info: str = "#3b82f6"
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "background": self.background,
            "surface": self.surface,
            "text": self.text,
            "text_secondary": self.text_secondary,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
            "info": self.info
        }
    
    @classmethod
    def dark_mode(cls) -> 'ColorPalette':
        """Version dark mode"""
        return cls(
            primary="#00ff88",
            secondary="#8b5cf6",
            accent="#3b82f6",
            background="#0f1215",
            surface="#1a1e24",
            text="#ffffff",
            text_secondary="#a0aec0"
        )


@dataclass
class Typography:
    """Système typographique"""
    font_family: str = "'Inter', -apple-system, sans-serif"
    font_family_mono: str = "'Fira Code', monospace"
    base_size: str = "16px"
    heading_scale: float = 1.25
    weights: Dict[str, int] = field(default_factory=lambda: {
        "light": 300,
        "regular": 400,
        "medium": 500,
        "bold": 700
    })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "font_family": self.font_family,
            "font_family_mono": self.font_family_mono,
            "base_size": self.base_size,
            "heading_scale": self.heading_scale,
            "weights": self.weights
        }


@dataclass
class Spacing:
    """Système d'espacement"""
    unit: int = 4
    xs: int = 4
    sm: int = 8
    md: int = 16
    lg: int = 24
    xl: int = 32
    xxl: int = 48
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "unit": self.unit,
            "xs": self.xs,
            "sm": self.sm,
            "md": self.md,
            "lg": self.lg,
            "xl": self.xl,
            "xxl": self.xxl
        }


@dataclass
class Breakpoint:
    """Points de rupture responsive"""
    sm: int = 640
    md: int = 768
    lg: int = 1024
    xl: int = 1280
    xxl: int = 1536
    
    def to_dict(self) -> Dict[str, int]:
        return {
            "sm": self.sm,
            "md": self.md,
            "lg": self.lg,
            "xl": self.xl,
            "xxl": self.xxl
        }


@dataclass
class DesignSystemSpec:
    """Spécification d'un système de design"""
    name: str
    system_type: DesignSystemType = DesignSystemType.CUSTOM
    colors: ColorPalette = field(default_factory=ColorPalette)
    typography: Typography = field(default_factory=Typography)
    spacing: Spacing = field(default_factory=Spacing)
    breakpoints: Breakpoint = field(default_factory=Breakpoint)
    accessibility_level: AccessibilityLevel = AccessibilityLevel.WCAG_AA
    dark_mode_support: bool = True
    rtl_support: bool = False
    motion_reduced: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "system_type": self.system_type.value,
            "colors": self.colors.to_dict(),
            "typography": self.typography.to_dict(),
            "spacing": self.spacing.to_dict(),
            "breakpoints": self.breakpoints.to_dict(),
            "accessibility_level": self.accessibility_level.value,
            "dark_mode_support": self.dark_mode_support,
            "rtl_support": self.rtl_support,
            "motion_reduced": self.motion_reduced,
            "metadata": self.metadata
        }


@dataclass
class ComponentStyle:
    """Style d'un composant"""
    name: str
    base_styles: Dict[str, str] = field(default_factory=dict)
    variants: Dict[str, Dict[str, str]] = field(default_factory=dict)
    states: Dict[str, Dict[str, str]] = field(default_factory=dict)
    responsive: Dict[str, Dict[str, str]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "base_styles": self.base_styles,
            "variants": self.variants,
            "states": self.states,
            "responsive": self.responsive
        }


@dataclass
class DesignGenerationResult:
    """Résultat de génération de design"""
    design_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    spec: DesignSystemSpec = field(default_factory=DesignSystemSpec)
    components: List[ComponentStyle] = field(default_factory=list)
    css: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    processing_time_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "design_id": self.design_id,
            "spec": self.spec.to_dict(),
            "components": [c.to_dict() for c in self.components],
            "css": self.css[:500] + "..." if len(self.css) > 500 else self.css,
            "created_at": self.created_at.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata
        }


@dataclass
class UiUxExpertStats:
    """Statistiques de l'expert UI/UX"""
    designs_created: int = 0
    designs_succeeded: int = 0
    designs_failed: int = 0
    components_styled: int = 0
    by_system_type: Dict[str, int] = field(default_factory=dict)
    total_processing_time: float = 0.0
    avg_processing_time: float = 0.0
    last_generation: Optional[datetime] = None
    start_time: datetime = field(default_factory=datetime.now)
    
    def record_generation(self, spec: DesignSystemSpec, components_count: int, 
                          processing_time: float, success: bool):
        """Enregistre une génération"""
        self.designs_created += 1
        if success:
            self.designs_succeeded += 1
            self.components_styled += components_count
        else:
            self.designs_failed += 1
            
        self.total_processing_time += processing_time
        self.avg_processing_time = self.total_processing_time / self.designs_created
        self.last_generation = datetime.now()
        
        # Statistiques par type
        system_type = spec.system_type.value
        self.by_system_type[system_type] = self.by_system_type.get(system_type, 0) + 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "designs_created": self.designs_created,
            "designs_succeeded": self.designs_succeeded,
            "designs_failed": self.designs_failed,
            "components_styled": self.components_styled,
            "by_system_type": self.by_system_type,
            "avg_processing_time_ms": round(self.avg_processing_time, 2),
            "total_processing_time_ms": round(self.total_processing_time, 2),
            "last_generation": self.last_generation.isoformat() if self.last_generation else None,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds()
        }


# ============================================================================
# SOUS-AGENT PRINCIPAL
# ============================================================================

class UiUxExpertSubAgent(BaseSubAgent):
    """
    Sous-agent expert UI/UX Design
    
    Crée des systèmes de design complets avec palettes de couleurs,
    typographie, espacements, et styles de composants accessibles.
    """
    
    def __init__(self, config_path: str = ""):
        """Initialise l'expert UI/UX"""
        # 🔧 CORRECTION : Résoudre le chemin absolu
        if not config_path:
            config_path = str(Path(__file__).parent / "config.yaml")
        elif not Path(config_path).is_absolute():
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
        self._subagent_display_name = config.get('display_name', "🎨 Expert UI/UX Design")
        self._subagent_description = config.get('description', "Création de systèmes de design et styles de composants")
        self._subagent_version = config.get('version', "2.0.0")
        self._subagent_category = config.get('category', "frontend_web3")
        self._subagent_capabilities = [
            "ui_ux.create_design_system",
            "ui_ux.generate_colors",
            "ui_ux.generate_typography",
            "ui_ux.style_component",
            "ui_ux.generate_responsive",
            "ui_ux.check_accessibility"
        ]
        
        # Templates
        self._templates = self._load_templates()
        
        # Statistiques
        self._stats = UiUxExpertStats()
        
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
        logger.info("Initialisation des composants UI/UX Expert...")
        
        # Démarrer la tâche de traitement
        self._processor_task = asyncio.create_task(self._processor_loop())
        
        self._components = {
            "version": self._subagent_version,
            "design_systems": ["material", "tailwind", "chakra", "radix"],
            "color_modes": ["light", "dark", "system"],
            "accessibility_levels": ["A", "AA", "AAA"],
            "frameworks": ["tailwind", "css", "scss", "styled-components"],
            "templates": list(self._templates.keys())
        }
        
        logger.info("✅ Composants UI/UX Expert initialisés")
        return True
        
    async def _initialize_components(self) -> bool:
        """Implémentation requise par BaseAgent"""
        return await self._initialize_subagent_components()

    def _get_capability_handlers(self) -> Dict[str, Callable]:
        """Retourne les handlers spécifiques"""
        return {
            "ui_ux.create_design_system": self._handle_create_design_system,
            "ui_ux.generate_colors": self._handle_generate_colors,
            "ui_ux.generate_typography": self._handle_generate_typography,
            "ui_ux.style_component": self._handle_style_component,
            "ui_ux.generate_responsive": self._handle_generate_responsive,
            "ui_ux.check_accessibility": self._handle_check_accessibility,
        }
    
    # ============================================================================
    # TEMPLATES
    # ============================================================================
    
    def _load_templates(self) -> Dict[str, str]:
        """Charge les templates de design"""
        return {
            "css_variables": """
:root {
  /* Couleurs */
  --color-primary: {primary};
  --color-secondary: {secondary};
  --color-accent: {accent};
  --color-background: {background};
  --color-surface: {surface};
  --color-text: {text};
  --color-text-secondary: {text_secondary};
  --color-success: {success};
  --color-warning: {warning};
  --color-error: {error};
  --color-info: {info};
  
  /* Typographie */
  --font-family: {font_family};
  --font-family-mono: {font_family_mono};
  --font-size-base: {base_size};
  
  /* Espacement */
  --spacing-xs: {spacing_xs}px;
  --spacing-sm: {spacing_sm}px;
  --spacing-md: {spacing_md}px;
  --spacing-lg: {spacing_lg}px;
  --spacing-xl: {spacing_xl}px;
  
  /* Breakpoints */
  --breakpoint-sm: {breakpoint_sm}px;
  --breakpoint-md: {breakpoint_md}px;
  --breakpoint-lg: {breakpoint_lg}px;
  --breakpoint-xl: {breakpoint_xl}px;
}

@media (prefers-color-scheme: dark) {{
  :root {{
    {dark_mode_colors}
  }}
}}
""",
            "component": """
.{component_name} {{
  /* Base styles */
  {base_styles}
  
  /* Variants */
  {variants}
  
  /* States */
  {states}
  
  /* Responsive */
  {responsive}
}}
""",
            "tailwind_config": """
module.exports = {{
  theme: {{
    extend: {{
      colors: {{
        primary: '{primary}',
        secondary: '{secondary}',
        accent: '{accent}',
        background: '{background}',
        surface: '{surface}',
        text: '{text}',
        'text-secondary': '{text_secondary}',
        success: '{success}',
        warning: '{warning}',
        error: '{error}',
        info: '{info}',
      }},
      fontFamily: {{
        sans: ['{font_family}'],
        mono: ['{font_family_mono}'],
      }},
      spacing: {{
        xs: '{spacing_xs}px',
        sm: '{spacing_sm}px',
        md: '{spacing_md}px',
        lg: '{spacing_lg}px',
        xl: '{spacing_xl}px',
      }},
      screens: {{
        sm: '{breakpoint_sm}px',
        md: '{breakpoint_md}px',
        lg: '{breakpoint_lg}px',
        xl: '{breakpoint_xl}px',
      }},
    }},
  }},
}};
"""
        }
    
    # ============================================================================
    # TÂCHES DE FOND
    # ============================================================================
    
    async def _processor_loop(self):
        """Boucle de traitement des designs"""
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
        if event_type == "design_created":
            logger.debug(f"✅ Design créé: {event.get('design_id')}")
    
    # ============================================================================
    # GÉNÉRATION DE DESIGN
    # ============================================================================
    
    async def create_design_system(self, spec: DesignSystemSpec) -> DesignGenerationResult:
        """
        Crée un système de design complet
        """
        start_time = time.time()
        result = DesignGenerationResult(spec=spec)
        
        try:
            # Ajouter les composants de base
            components = [
                ComponentStyle(name="Button"),
                ComponentStyle(name="Card"),
                ComponentStyle(name="Input"),
                ComponentStyle(name="Modal"),
                ComponentStyle(name="Typography")
            ]
            result.components = components
            
            # Générer le CSS
            css_template = self._templates["css_variables"]
            dark_mode_colors = ""
            if spec.dark_mode_support:
                dark = ColorPalette.dark_mode()
                dark_mode_colors = "\n".join([
                    f"  --color-{k}: {v};" for k, v in dark.to_dict().items()
                ])
            
            result.css = css_template.format(
                primary=spec.colors.primary,
                secondary=spec.colors.secondary,
                accent=spec.colors.accent,
                background=spec.colors.background,
                surface=spec.colors.surface,
                text=spec.colors.text,
                text_secondary=spec.colors.text_secondary,
                success=spec.colors.success,
                warning=spec.colors.warning,
                error=spec.colors.error,
                info=spec.colors.info,
                font_family=spec.typography.font_family,
                font_family_mono=spec.typography.font_family_mono,
                base_size=spec.typography.base_size,
                spacing_xs=spec.spacing.xs,
                spacing_sm=spec.spacing.sm,
                spacing_md=spec.spacing.md,
                spacing_lg=spec.spacing.lg,
                spacing_xl=spec.spacing.xl,
                breakpoint_sm=spec.breakpoints.sm,
                breakpoint_md=spec.breakpoints.md,
                breakpoint_lg=spec.breakpoints.lg,
                breakpoint_xl=spec.breakpoints.xl,
                dark_mode_colors=dark_mode_colors
            )
            
            result.success = True
            
            # Enregistrer les stats
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(spec, len(components), processing_time, True)
            
            # Journaliser l'événement
            await self._log_event("design_created", {
                "design_id": result.design_id,
                "name": spec.name,
                "type": spec.system_type.value,
                "components": len(components),
                "processing_time_ms": processing_time
            })
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            processing_time = (time.time() - start_time) * 1000
            result.processing_time_ms = processing_time
            self._stats.record_generation(spec, 0, processing_time, False)
            logger.error(f"❌ Erreur création design system: {e}")
        
        return result
    
    async def generate_colors(self, base_color: str = "#00ff88", mode: str = "light") -> Dict[str, Any]:
        """Génère une palette de couleurs"""
        palette = ColorPalette(primary=base_color)
        if mode == "dark":
            palette = ColorPalette.dark_mode()
            palette.primary = base_color
        
        return {
            "success": True,
            "palette": palette.to_dict(),
            "mode": mode
        }
    
    async def generate_typography(self, font_family: str = "Inter") -> Dict[str, Any]:
        """Génère un système typographique"""
        typography = Typography(font_family=f"'{font_family}', sans-serif")
        
        return {
            "success": True,
            "typography": typography.to_dict()
        }
    
    async def style_component(self, name: str, **kwargs) -> Dict[str, Any]:
        """Génère les styles pour un composant"""
        component = ComponentStyle(name=name)
        
        # Styles de base selon le type de composant
        if name == "Button":
            component.base_styles = {
                "display": "inline-flex",
                "alignItems": "center",
                "justifyContent": "center",
                "padding": "var(--spacing-sm) var(--spacing-md)",
                "borderRadius": "4px",
                "fontWeight": "500",
                "cursor": "pointer",
                "transition": "all 0.2s"
            }
            component.variants = {
                "primary": {
                    "backgroundColor": "var(--color-primary)",
                    "color": "white"
                },
                "secondary": {
                    "backgroundColor": "var(--color-secondary)",
                    "color": "white"
                },
                "outline": {
                    "border": "2px solid var(--color-primary)",
                    "color": "var(--color-primary)",
                    "backgroundColor": "transparent"
                }
            }
            component.states = {
                "hover": {
                    "opacity": "0.9",
                    "transform": "translateY(-1px)"
                },
                "active": {
                    "transform": "translateY(0)"
                },
                "disabled": {
                    "opacity": "0.5",
                    "cursor": "not-allowed"
                }
            }
        
        return {
            "success": True,
            "component": component.to_dict()
        }
    
    async def generate_responsive(self, styles: Dict[str, Any]) -> Dict[str, Any]:
        """Génère des styles responsifs"""
        breakpoints = Breakpoint()
        
        responsive = {}
        for size, value in breakpoints.to_dict().items():
            if size in styles:
                responsive[size] = styles[size]
        
        return {
            "success": True,
            "responsive": responsive,
            "breakpoints": breakpoints.to_dict()
        }
    
    async def check_accessibility(self, colors: Dict[str, str], level: str = "AA") -> Dict[str, Any]:
        """Vérifie l'accessibilité des contrastes"""
        issues = []
        
        # Vérifications basiques de contraste
        if "text" in colors and "background" in colors:
            issues.append("Contraste à vérifier avec des outils spécialisés")
        
        if level == "AAA":
            issues.append("Niveau AAA nécessite des contrastes très élevés")
        
        return {
            "success": True,
            "level": level,
            "compliant": len(issues) == 0,
            "issues": issues,
            "recommendations": [
                "Utiliser des outils comme WebAIM Contrast Checker",
                "Tester avec des lecteurs d'écran",
                "Vérifier la navigation au clavier"
            ]
        }
    
    # ============================================================================
    # HANDLERS DE CAPACITÉS
    # ============================================================================
    
    async def _handle_create_design_system(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un système de design"""
        colors = ColorPalette(
            primary=params.get("primary_color", "#00ff88"),
            background=params.get("background_color", "#ffffff"),
            text=params.get("text_color", "#1a1e24")
        )
        
        if params.get("dark_mode", True):
            colors = ColorPalette.dark_mode()
        
        spec = DesignSystemSpec(
            name=params.get("name", "DesignSystem"),
            system_type=DesignSystemType.from_string(params.get("type", "custom")),
            colors=colors,
            accessibility_level=AccessibilityLevel.from_string(params.get("accessibility", "AA")),
            dark_mode_support=params.get("dark_mode", True),
            metadata=params.get("metadata", {})
        )
        
        result = await self.create_design_system(spec)
        return result.to_dict()
    
    async def _handle_generate_colors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère une palette de couleurs"""
        base = params.get("base_color", "#00ff88")
        mode = params.get("mode", "light")
        
        result = await self.generate_colors(base, mode)
        return result
    
    async def _handle_generate_typography(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère une typographie"""
        font = params.get("font_family", "Inter")
        
        result = await self.generate_typography(font)
        return result
    
    async def _handle_style_component(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère les styles d'un composant"""
        name = params.get("name", "Button")
        
        result = await self.style_component(name, **params.get("options", {}))
        return result
    
    async def _handle_generate_responsive(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Génère des styles responsifs"""
        styles = params.get("styles", {})
        
        result = await self.generate_responsive(styles)
        return result
    
    async def _handle_check_accessibility(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Vérifie l'accessibilité"""
        colors = params.get("colors", {})
        level = params.get("level", "AA")
        
        result = await self.check_accessibility(colors, level)
        return result
    
    # ============================================================================
    # GESTION DES MESSAGES
    # ============================================================================
    
    def _get_standard_handlers(self) -> Dict[str, Callable]:
        """Retourne les handlers standards communs"""
        return {
            f"{self.name}.status": self._handle_status,
            f"{self.name}.metrics": self._handle_metrics,
            f"{self.name}.health": self._handle_health,
            f"{self.name}.capabilities": self._handle_capabilities,
            f"{self.name}.info": self._handle_info,
            f"{self.name}.stats": self._handle_stats,
        }
    
    async def _handle_status(self, message: Message) -> Message:
        """Retourne le statut général"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={
                'status': self._status.value,
                'initialized': self._initialized,
                'display_name': self._subagent_display_name,
                'stats': self._stats.to_dict()
            },
            message_type=f"{self.name}.status_response",
            correlation_id=message.message_id
        )
    
    async def _handle_metrics(self, message: Message) -> Message:
        """Retourne les métriques"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=self._stats.to_dict(),
            message_type=f"{self.name}.metrics_response",
            correlation_id=message.message_id
        )
    
    async def _handle_health(self, message: Message) -> Message:
        """Retourne l'état de santé"""
        health = await self.health_check()
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=health,
            message_type=f"{self.name}.health_response",
            correlation_id=message.message_id
        )
    
    async def _handle_capabilities(self, message: Message) -> Message:
        """Liste les capacités disponibles"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content={
                'capabilities': self._subagent_capabilities,
                'version': self._subagent_version,
                'display_name': self._subagent_display_name,
                'category': self._subagent_category
            },
            message_type=f"{self.name}.capabilities_response",
            correlation_id=message.message_id
        )
    
    async def _handle_info(self, message: Message) -> Message:
        """Retourne les informations générales"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=self.get_agent_info(),
            message_type=f"{self.name}.info_response",
            correlation_id=message.message_id
        )
    
    async def _handle_stats(self, message: Message) -> Message:
        """Retourne les statistiques détaillées"""
        return Message(
            sender=self.name,
            recipient=message.sender,
            content=self._stats.to_dict(),
            message_type=f"{self.name}.stats_response",
            correlation_id=message.message_id
        )
    
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

            # Handlers standards
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
        event = {"type": event_type, "timestamp": datetime.now().isoformat(), "data": data}
        await self._event_queue.put(event)
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
        """Arrête le sous-agent"""
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