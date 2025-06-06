import logging
from abc import ABC, abstractmethod

from integrations.models import Integration, CredentialsEntity, ContextualData


class BaseProviderBackend(ABC):
    _id = None
    name = None
    category = None
    order = 1000
    allowed_credentials_types = []
    listening_events = []

    """
    Classe base para todos os providers de dados contextuais.
    Cada integração (plugin) deve herdar desta classe e implementar os métodos obrigatórios.
    """

    def __init__(self, integration: Integration = None, credentials: CredentialsEntity = None):
        self.integration = integration
        self.credentials = credentials

    """Propriedades e métodos básicos."""

    @property
    def config(self):
        """Retorna o objeto de configuração validado (Pydantic)."""
        return self.get_provider_backend_data_obj()

    @classmethod
    def get_category(cls):
        """
        Retorna a categoria da integração.
        """
        return cls.category or "unknown"

    """Métodos abstratos que devem ser implementados por cada provider."""

    @abstractmethod
    def get_provider_backend_data_config(self):
        """Retorna a classe do schema Pydantic para provider_backend_data."""
        raise NotImplementedError

    @abstractmethod
    def fetch(self):
        """
        Método abstrato para buscar dados do provider.
        """
        raise NotImplementedError

    """Métodos de acesso e normalização de dados."""

    def get_provider_backend_data_obj(self):
        """
        Converte provider_backend_data em objeto Pydantic usando o schema definido pelo provider.
        """
        schema_model = self.get_provider_backend_data_config()
        data = self.integration.provider_backend_data if self.integration else {}
        return schema_model(**(data or {}))

    def normalize(self, raw_data: dict) -> dict:
        """
        (Opcional) Método para normalizar dados crus. Override se necessário.
        """
        return raw_data

    def serialize_data(self, data: dict) -> dict:
        """
        Serializa os dados para um formato JSON serializável.
        Pode ser sobrescrito por cada provider.
        """
        from datetime import datetime, date

        if isinstance(data, dict):
            return {
                key: (value.isoformat() if isinstance(value, (datetime, date)) else value)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                (item.isoformat() if isinstance(item, (datetime, date)) else item)
                for item in data
            ]
        elif isinstance(data, (datetime, date)):
            return data.isoformat()
        return data

    """Métodos de validação e schema."""

    @classmethod
    @abstractmethod
    def get_schema_dict(cls, integration=None):
        """
        Retorna o schema de configurações para o provider.
        Pode ser sobrescrito por cada provider.
        """
        return {
            'type': 'object',
            'properties': cls.get_additional_schema_properties(),
            'additionalProperties': True
        }

    @classmethod
    def get_additional_schema_properties(cls):
        """
        Método gancho: Pode ser sobrescrito para adicionar propriedades ao esquema.
        """
        return {}

    @classmethod
    def validate_data(cls, data):
        """
        Método Template: Valida os dados. Subclasses podem estender a lógica de validação.
        """
        cls.validate_required_fields(data)
        return data

    @classmethod
    def get_required_fields(cls):
        """
        Retorna uma lista de campos obrigatórios.
        Subclasses podem sobrescrever este método para definir campos específicos.
        """
        return []

    @classmethod
    def validate_required_fields(cls, data):
        """
        Método gancho: Pode ser sobrescrito para validar campos específicos.
        """
        for field in cls.get_required_fields():
            if field not in data:
                raise ValueError(f"Campo obrigatório '{field}' não encontrado.")

    @classmethod
    def version_data(cls, normalized_data: dict) -> str:
        """
        (Opcional) Gera um hash para controle de versionamento dos dados.
        """
        import hashlib
        import json
        raw = json.dumps(normalized_data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    """Métodos de criação e manipulação de eventos contextuais."""

    def get_or_create_event(self, event_type, event_date, location=None, city=None, category=None, extra_fields=None):
        """
        Obtém ou cria um evento contextual genérico.
        """
        from integrations.models import ContextualEvent

        event, created = ContextualEvent.objects.update_or_create(
            event_type=event_type,
            event_date=event_date,
            location=location,
            city=city,
            defaults={
                "category": category,
                "integration": self.integration,
                "extra_fields": extra_fields or {},
            }
        )
        if created:
            self.save_log(
                success=True,
                message=f"Evento '{event_type}' criado.",
                method="consume",
                records_imported=1,
                request_data={"event_type": event_type, "event_date": event_date, "extra_fields": extra_fields},
            )

        return event

    def create_contextual_data(self, event, normalized_data):
        """
        Cria um registro de ContextualData vinculado ao evento.
        """
        last = ContextualData.objects.filter(event=event, integration=self.integration).order_by('-version').first()
        next_version = (last.version + 1 if last else 1)

        contextual_data = ContextualData.objects.create(
            event=event,
            integration=self.integration,
            version=next_version,
            extra_fields={**normalized_data, "data_hash": self.version_data(normalized_data)}
        )
        return contextual_data

    """Métodos de logging e eventos."""

    def save_log(
            self,
            success: bool = True,
            message: str = None,
            method: str = None,
            records_imported: int = 0,
            request_data: dict = None,
            response_data: dict = None,
    ):
        """
        Registra a requisição no banco de dados.
        """
        if self.integration and not self.integration.enable_logging:
            return

        try:
            from integrations.models import IntegrationLog
            IntegrationLog.objects.create(
                integration=self.integration,
                success=success,
                error=not success,
                message=message or "Requisição realizada.",
                method=method or IntegrationLog.MethodChoices.FETCH,
                records_imported=records_imported,
                request_data=self.serialize_data(request_data) or {},
                response_data=self.serialize_data(response_data) or {},
            )
        except Exception as e:
            logging.exception(f"Erro ao salvar log para integração {getattr(self.integration, 'name', None)}: {e}")
