from pathlib import Path


class PluginRegistry:
    def __init__(self):
        self._credentials = None
        self._providers = None

    def _discover_plugins(self, base_class, package_name, package_path):
        """
        Descobre e importa automaticamente plugins que herdam base_class
        em package_name localizado em package_path (recursivo).
        Retorna um dict {plugin_id: plugin_class}.
        """
        import importlib
        import inspect
        import pkgutil

        plugins = {}
        for finder, name, ispkg in pkgutil.walk_packages([str(package_path)], prefix=package_name + "."):
            try:
                module = importlib.import_module(name)
            except Exception as e:
                print(f"Erro ao importar {name}: {e}")
                raise
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, base_class) and obj is not base_class:
                    plugins[obj.id] = obj
        return plugins

    def _load_credentials_types(self):
        """Carrega e armazena as credenciais se ainda não carregadas."""
        if self._credentials is None:
            package_name = "integrations.credentials"
            package_path = Path(__file__).parent / "credentials"

            from integrations.credentials.base import BaseCredentialsType
            self._credentials = self._discover_plugins(BaseCredentialsType, package_name, package_path)

    def _load_providers_backends(self):
        """Carrega e armazena os providers se ainda não carregados."""
        if self._providers is None:
            package_name = "integrations.providers"
            package_path = Path(__file__).parent / "providers"

            from integrations.providers.base import BaseProviderBackend
            self._providers = self._discover_plugins(BaseProviderBackend, package_name, package_path)

    def get_credentials_types_choices(self):
        """Retorna lista de choices [(id, name), ...] para tipos de credenciais, para usar no form."""
        self._load_credentials_types()
        choices = [(ct.id, ct.name) for ct in self._credentials.values()]
        choices = sorted(choices, key=lambda x: x[1])
        choices.insert(0, ('', 'Selecione um tipo de credencial'))
        return choices

    def get_provider_backends_choices(self):
        """Retorna lista de choices [(id, name), ...] para providers, para usar no form."""
        self._load_providers_backends()
        choices = [(cls.id, cls.name) for cls in self._providers.values()]
        choices = sorted(choices, key=lambda x: x[1])
        choices.insert(0, ('', 'Selecione um provedor'))
        return choices

    def get_credentials_type(self, id: str):
        """Retorna a classe da credencial pelo id."""
        self._load_credentials_types()
        return self._credentials.get(id)

    def get_provider_backend(self, id: str):
        """Retorna a classe do provider backend pelo id."""
        self._load_providers_backends()
        return self._providers.get(id)


plugin_registry = PluginRegistry()
