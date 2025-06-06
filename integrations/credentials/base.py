from abc import ABC, abstractmethod

from integrations.models import CredentialsEntity


class BaseCredentialsType(ABC):
    """
    Classe base para tipos de credenciais usadas nos providers.
    Cada credencial concreta deve herdar e implementar os métodos obrigatórios.
    """

    def __init__(self, instance: CredentialsEntity):
        """
        instance: instância do modelo CredentialsEntity
        """
        self.instance = instance

    """Propriedades que devem ser implementadas por cada tipo de credencial."""

    @abstractmethod
    def get_name(self) -> str:
        """Nome legível da credencial para exibição no admin."""
        pass

    @classmethod
    def get_credentials_schema(cls):
        """
        Retorna a classe do schema público (Pydantic).
        Deve ser sobrescrito pelas subclasses.
        """
        raise NotImplementedError("Subclasses devem implementar este método.")

    @classmethod
    def get_credentials_private_schema(cls):
        """
        Retorna a classe do schema privado (Pydantic).
        Retorna None por padrão se não for implementado.
        """
        raise NotImplementedError("Subclasses devem implementar este método.")

    def validate_credentials(self, credentials: dict):
        """
        Valida os dados de autenticação.
        Deve ser sobrescrito pelas subclasses.
        """
        raise NotImplementedError("Subclasses devem implementar este método.")

    """Métodos utilitários para acesso aos dados de credenciais."""

    def get_credentials_type_data_obj(self):
        """
        Converte os dados públicos do tipo de credencial (dicionário)
        em objeto Pydantic, usando o schema definido.
        """
        schema_model = self.get_credentials_schema()
        data = self.instance.credentials_type_data or {}

        if not schema_model:
            return None

        try:
            return schema_model(**data)
        except Exception as e:
            raise ValueError(f"Erro ao instanciar o schema público: {e}")

    def get_credentials_type_private_data_obj(self):
        """
        Converte os dados privados do tipo de credencial (dicionário)
        em objeto Pydantic, usando o schema privado definido.
        """
        schema_model = self.get_credentials_private_schema()
        private_data = self.instance.credentials_type_private_data or {}

        if not schema_model:
            return None

        try:
            return schema_model(**private_data)
        except Exception as e:
            raise ValueError(f"Erro ao instanciar o schema privado: {e}")

    """Métodos opcionais que podem ser implementados por cada tipo de credencial."""

    def validate_data(self, data: dict):
        """
        (Opcional) Valida dados adicionais da integração, se necessário.
        """
        raise NotImplementedError

    def get_auth_headers(self) -> dict:
        """
        (Opcional) Gera headers de autenticação para chamadas.
        """
        return {}
