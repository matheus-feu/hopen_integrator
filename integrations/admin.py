from django.contrib import admin
from django.utils.text import slugify
from django_jsonform.forms.fields import JSONFormField

from integrations.admin_forms import (
    CredentialsTypeAdminForm,
    BaseCredentialsEntityAdminForm,
    BaseIntegrationAdminForm,
    IntegrationProviderBackendAdminForm
)
from integrations.registry import plugin_registry
from .models import (
    CredentialsEntity,
    Integration,
    IntegrationLog,
    ContextualEvent,
    ContextualData
)


@admin.register(CredentialsEntity)
class CredentialsEntityAdmin(admin.ModelAdmin):
    list_display = ('name', 'credentials_type_id', 'is_active',)
    list_filter = ('is_active',)
    search_fields = ('name',)
    list_editable = ('is_active',)
    exclude = ('properties',)

    def save_model(self, request, obj, form, change):
        if not obj.handle:
            obj.handle = slugify(obj.name)
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        credentials_type_id = request.GET.get('credentials_type_id') or (obj and obj.credentials_type_id)
        credentials_type_cls = plugin_registry.get_credentials_type(credentials_type_id)

        if not credentials_type_cls:
            self.prepopulated_fields = {}
            return CredentialsTypeAdminForm

        # Validar se o tipo de credencial é válido
        schema_cls = credentials_type_cls.get_credentials_schema()
        try:
            schema = schema_cls.schema() if schema_cls and hasattr(schema_cls, 'schema') else {}
            if not isinstance(schema, (dict, list)):
                raise ValueError("Schema público inválido.")
        except Exception as e:
            schema = {}

        # Validar se o schema privado é válido
        private_schema_cls = credentials_type_cls.get_credentials_private_schema()
        try:
            private_schema = (
                private_schema_cls.schema()
                if private_schema_cls and hasattr(private_schema_cls, 'schema')
                else None
            )
            if not isinstance(private_schema, (dict, list)):
                private_schema = None
        except Exception:
            private_schema = None

        # Configurar o formulário com os campos necessários
        self.prepopulated_fields = {'handle': ('name',)}
        form = BaseCredentialsEntityAdminForm
        form.base_fields['credentials_type_data'] = JSONFormField(schema=schema, label='Configurações Personalizadas')

        # Adicionar ou remover o campo de acordo com a validação do schema privado
        if private_schema is None:
            form.base_fields.pop('credentials_type_private_data', None)
        else:
            form.base_fields['credentials_type_private_data'] = JSONFormField(
                schema=private_schema,
                label='Configurações Privadas',
                required=False,
            )

        if not obj:
            form.base_fields['credentials_type_id'].initial = credentials_type_cls.id
            form.base_fields['name'].initial = credentials_type_cls.name
        if obj:
            form.base_fields['credentials_type_id'].disabled = True
            form.base_fields['handle'].disabled = True

        return form


@admin.register(Integration)
class IntegrationAdmin(admin.ModelAdmin):
    list_display = ('get_provider', 'is_active', 'enable_logging')
    list_filter = ('is_active', 'enable_logging')
    list_editable = ('is_active', 'enable_logging')
    exclude = ('name',)
    prepopulated_fields = {}

    def save_model(self, request, obj, form, change):
        if not obj.handle and obj.name:
            obj.handle = slugify(obj.name)
        super().save_model(request, obj, form, change)

    def get_provider(self, obj):
        provider = plugin_registry.get_provider_backend(obj.provider_backend_id)
        return provider.name if provider else '-'

    get_provider.short_description = 'Provedor'

    def get_form(self, request, obj=None, **kwargs):
        provider_backend_id = request.GET.get('provider_backend_id') or (obj and obj.provider_backend_id)
        provider_backend = plugin_registry.get_provider_backend(provider_backend_id)

        if not provider_backend:
            self.prepopulated_fields = {}
            return IntegrationProviderBackendAdminForm

        self.prepopulated_fields = {'handle': ('name',)}
        form = BaseIntegrationAdminForm
        schema_fields = provider_backend.get_schema_dict(integration=obj)

        form.base_fields['provider_backend_data'] = JSONFormField(
            schema=schema_fields,
            label='Configurações Personalizadas',
            required=False,
        )

        allowed_credentials_types = (
            plugin_registry.get_provider_backend(obj.provider_backend_id).allowed_credentials_types
            if obj else provider_backend.allowed_credentials_types
        )
        credentials_qs = CredentialsEntity.objects.filter(
            credentials_type_id__in=allowed_credentials_types
        )
        form.base_fields['credentials'].queryset = credentials_qs

        if not obj:
            form.base_fields['provider_backend_id'].initial = provider_backend.id
            form.base_fields['name'].initial = provider_backend.name
            form.base_fields['handle'].initial = provider_backend.handle
        if obj:
            form.base_fields['provider_backend_id'].disabled = True
            form.base_fields['handle'].disabled = True

        return form


@admin.register(IntegrationLog)
class IntegrationLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "integration",
        "method",
        "success",
        "message",
        "records_imported",
    )
    list_filter = ("integration", "method", "success", "timestamp")
    search_fields = ("integration__name", "message", "request_data", "response_data")
    readonly_fields = (
        "timestamp",
        "integration",
        "method",
        "success",
        "message",
        "request_data",
        "response_data",
        "records_imported",
    )
    date_hierarchy = "timestamp"


@admin.register(ContextualEvent)
class ContextualEventAdmin(admin.ModelAdmin):
    list_display = ('uid', 'event_type', 'event_date', 'integration', 'created_at')
    search_fields = ('event_type', 'integration__name')
    list_filter = ('event_type', 'event_date', 'integration')
    readonly_fields = ('extra_fields',)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'extra_fields':
            return JSONFormField(schema={}, disabled=True, label='Atributos do Evento')
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(ContextualData)
class ContextualDataAdmin(admin.ModelAdmin):
    list_display = ('uid', 'event', 'integration', 'version', 'fetched_at')
    search_fields = ('event__event_type', 'integration__name')
    list_filter = ('integration', 'version', 'fetched_at')
    readonly_fields = ('extra_fields',)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'extra_fields':
            return JSONFormField(schema={}, disabled=True, label='Dados Contextuais')
        return super().formfield_for_dbfield(db_field, request, **kwargs)
