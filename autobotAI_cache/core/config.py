from autobotAI_cache.config.defaults import DEFAULT_CONFIG
from autobotAI_cache.backends import BackendRegistry


class Config:
    def __init__(self):
        self._config = DEFAULT_CONFIG.copy()
        self._backend = None
    
    def reset(self):
        self._config = DEFAULT_CONFIG.copy()
        self._backend = None

    def configure(self, **kwargs):
        """Update configuration settings"""
        self._config.update(kwargs)
        self._backend = None  # Reset backend on config change

    def __getattr__(self, name):
        """Direct access to config values"""
        if name in self._config:
            return self._config[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    @property
    def backend(self):
        """Lazy-loaded backend instance"""
        if not self._backend:
            backend_name = self._config["BACKEND"]
            backend_cls = BackendRegistry.get_backend(backend_name)
            self._backend = backend_cls(**self._config.get("BACKEND_OPTIONS", {}))
        return self._backend
    
    @property
    def backend_name(self):
        """Name of the backend"""
        return self._config["BACKEND"]


# Global configuration instance
settings = Config()
