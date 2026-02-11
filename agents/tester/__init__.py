def __init__(self, config_path: str = ""):
    """
    Initialise l'agent de test
    
    Args:
        config_path: Chemin vers le fichier de configuration
    """
    # Appel du parent
    super().__init__(config_path)
    
    # Configuration par défaut
    if not self.config:
        self._default_config = self._get_default_config()
        if hasattr(self, '_config'):
            self._config = self._default_config
    
    self._logger.info(f"Agent tester créé (config: {config_path})")
    
    # État de l'agent - Utiliser _status au lieu de status
    self._status = AgentStatus.CREATED
    self.test_frameworks = {}
    self.test_suites = {}
    self.test_results = []
    self.security_findings = []
    self.reports = []
    self.running_tests = {}
    
    # Initialisation des composants
    self._initialize_test_templates()
    self._initialize_framework_detectors()
    
    self._logger.info("Agent Tester initialisé avec la configuration de " + config_path)
    self._logger.info(f"Changement de statut: {self._status.value} -> initializing")
    self._logger.info("Initialisation de l'agent tester...")
    
    self._status = AgentStatus.INITIALIZING
    
    # Vérification des dépendances
    self._check_dependencies()
    
    self._logger.info("Initialisation des composants du TesterAgent...")
    # Composants spécifiques
    self.components = {
        "test_generator": self._init_test_generator(),
        "test_executor": self._init_test_executor(),
        "security_scanner": self._init_security_scanner(),
        "coverage_analyzer": self._init_coverage_analyzer(),
        "report_generator": self._init_report_generator()
    }
    self._logger.info("Composants du TesterAgent initialisés avec succès")
    
    self._status = AgentStatus.READY
    self._logger.info(f"Changement de statut: initializing -> {self._status.value}")
    self._logger.info("Agent tester initialisé avec succès")