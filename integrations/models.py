from django.db import models

from core.models import BaseModel
from .registry import plugin_registry
from .utils import get_uuid


class CredentialsEntity(BaseModel):
    """
    Model to store credentials for integrations.
    """

    uid = models.UUIDField(primary_key=True, default=get_uuid, editable=False)
    name = models.CharField(max_length=255, verbose_name='Nome')
    handle = models.CharField(max_length=32, verbose_name='Identificador')

    credentials_type_id = models.CharField(max_length=32, verbose_name='Tipo de Credencial')
    credentials_type_data = models.JSONField(default=dict, verbose_name='Dados da Credencial')
    credentials_type_private_data = models.JSONField(default=dict, verbose_name='Dados Privados')

    is_active = models.BooleanField(default=False, verbose_name='Ativo?')
    last_checked_at = models.DateTimeField(null=True, blank=True, editable=False, verbose_name='Última Verificação')
    last_success_at = models.DateTimeField(null=True, blank=True, editable=False, verbose_name='Último Sucesso')
    last_error_at = models.DateTimeField(null=True, blank=True, editable=False, verbose_name='Último Erro')
    last_error = models.TextField(null=True, blank=True, editable=False, verbose_name='Última Mensagem de Erro')

    class Meta:
        unique_together = ('handle',)
        verbose_name = 'Credenciais'
        verbose_name_plural = 'Credenciais'

    def __str__(self):
        return self.name or self.handle

    def get_credential_backend(self):
        if hasattr(self, '_credential_backend'):
            return self._credential_backend

        backend_cls = plugin_registry.get_provider_backend(self.credentials_type_id)
        if backend_cls is None:
            return None

        self._credential_backend = backend_cls(self)
        return self._credential_backend

    def clean(self):
        provider_backend = plugin_registry.get_provider_backend(self.credentials_type_id)
        if provider_backend and self.credentials_type_id not in provider_backend.allowed_credentials_types:
            raise ValueError(
                f"Tipo de credencial '{self.credentials_type_id}' não é permitido para o provedor {provider_backend.name}.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Integration(models.Model):
    uid = models.UUIDField(primary_key=True, default=get_uuid, editable=False)
    name = models.CharField(max_length=255, verbose_name='Nome')
    handle = models.CharField(
        max_length=32,
        unique=True,
        verbose_name='Identificador',
        help_text="Identificador único para a integração, usado em URLs e referências."
    )
    enable_logging = models.BooleanField(
        default=True,
        verbose_name="Habilitar Logging",
        help_text="Habilita o registro de logs para depuração."
    )
    provider_backend_id = models.CharField(max_length=32, verbose_name='ID do Provedor Backend')
    provider_backend_data = models.JSONField(default=dict, verbose_name='Dados do Backend do Provedor')
    credentials = models.ForeignKey(
        CredentialsEntity,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='integrations'
    )
    is_active = models.BooleanField(default=False, verbose_name='Ativo?')

    def __str__(self):
        return self.name or self.handle


class ContextualEvent(models.Model):
    """
    Representa um evento único e normalizado, deduplicado a partir de múltiplas fontes.
    Exemplo: "Chuva em São Paulo em 2024-06-10" ou "Show do artista X em BH".
    Centraliza informações principais do evento, como tipo, data, local, cidade e categoria.
    Pode ser referenciado por vários dados contextuais coletados de diferentes integrações.
    """
    uid = models.UUIDField(primary_key=True, default=get_uuid, editable=False)
    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='events',
    )
    event_type = models.CharField(max_length=100, verbose_name='Tipo do Evento', default='desconhecido')
    event_date = models.DateField(null=True, blank=True, verbose_name='Data do Evento')
    location = models.CharField(max_length=255, null=True, blank=True, verbose_name='Localização do Evento')
    city = models.CharField(max_length=255, null=True, blank=True, verbose_name='Cidade do Evento')
    category = models.CharField(max_length=100, null=True, blank=True, verbose_name='Categoria do Evento')
    extra_fields = models.JSONField(default=dict, blank=True, verbose_name='Atributos do Evento')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    def __str__(self):
        return f"{self.event_type} - {self.event_date or ''} ({self.uid})"


class ContextualData(models.Model):
    """
    Armazena os dados contextuais coletados para um evento, permitindo versionamento e histórico.
    Cada registro representa uma coleta de dados (ex: clima, informações de evento) para um ContextualEvent,
    podendo ser proveniente de diferentes integrações e em diferentes versões.
    Permite rastrear a evolução dos dados e manter histórico de coletas.
    """
    uid = models.UUIDField(primary_key=True, default=get_uuid, editable=False)
    event = models.ForeignKey(ContextualEvent, on_delete=models.CASCADE, related_name='contextual_data')
    integration = models.ForeignKey('Integration', on_delete=models.CASCADE, related_name='contextual_data')
    version = models.PositiveIntegerField(default=1, verbose_name='Versão')
    fetched_at = models.DateTimeField(auto_now_add=True, verbose_name='Data de Coleta')
    extra_fields = models.JSONField(default=dict, blank=True, verbose_name='Dados Contextuais')

    class Meta:
        unique_together = ('event', 'integration', 'version')
        ordering = ['-fetched_at']

    def __str__(self):
        return f"Data v{self.version} - {self.integration.name} para evento {self.event.uid}"


class IntegrationLog(models.Model):
    class MethodChoices(models.TextChoices):
        FETCH = 'fetch', 'Fetch'
        CONSUME = 'consume', 'Consume'
        IMPORT = 'import', 'Import'

    uid = models.UUIDField(primary_key=True, default=get_uuid, editable=False)
    integration = models.ForeignKey(
        Integration,
        on_delete=models.CASCADE,
        related_name='logs',
        verbose_name='Integração'
    )
    success = models.BooleanField(default=False, verbose_name='Sucesso?')
    error = models.BooleanField(default=False, verbose_name='Erro?')
    message = models.TextField(null=True, blank=True, verbose_name='Mensagem de Log')
    method = models.CharField(
        max_length=50,
        choices=MethodChoices.choices,
        default=MethodChoices.FETCH,
        verbose_name='Método'
    )
    records_imported = models.PositiveIntegerField(default=0, verbose_name='Registros Importados')
    request_data = models.JSONField(default=dict, blank=True, verbose_name='Dados da Requisição')
    response_data = models.JSONField(default=dict, blank=True, verbose_name='Dados da Resposta')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Data e Hora')

    def __str__(self):
        status = "Sucesso" if self.success else "Erro"
        return f"{self.integration.name} - {status} em {self.timestamp}"
