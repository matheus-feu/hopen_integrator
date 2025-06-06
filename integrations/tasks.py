import logging

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

from integrations.models import Integration
from integrations.registry import plugin_registry

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, soft_time_limit=300, queue='high_priority')
def fetch_all_active_integrations(self):
    try:
        self.update_state(
            state='STARTED',
            meta={
                'status': 'Iniciando a importação de integrações.',
                'task_id': self.request.id
            }
        )
        integrations = Integration.objects.filter(is_active=True)
        if not integrations:
            logger.info("[INFO] Nenhuma integração ativa encontrada.")
            self.update_state(state='FAILURE', meta={'status': 'Nenhuma integração ativa encontrada.'})
            return

        logger.info(f"[INFO] Iniciando a importação de {len(integrations)} integrações ativas.")
        for integration in integrations:
            try:
                self.update_state(state='PROGRESS', meta={'status': f'Processando integração {integration.name}.'})
                provider_cls = plugin_registry.get_provider_backend(integration.provider_backend_id)
                provider_backend = provider_cls(integration=integration, credentials=integration.credentials)
                normalized_data_list = provider_backend.fetch()

                if not normalized_data_list:
                    logger.warning(f"[AVISO] Nenhum dado retornado para a integração '{integration.name}'.")
                    continue

                for normalized_data in normalized_data_list:
                    if not all(key in normalized_data for key in ["city", "timestamp"]):
                        logger.error(
                            f"[ERRO] Dados normalizados incompletos para integração '{integration.name}': {normalized_data}")
                        continue

                    try:
                        category = provider_backend.get_category()
                        event_type = f"{normalized_data['city']} - {category}"
                        event_date = normalized_data["timestamp"].date().isoformat()
                        city = normalized_data["city"]

                        normalized_data_serializable = provider_backend.serialize_data(normalized_data)

                        event = provider_backend.get_or_create_event(
                            event_type=event_type,
                            event_date=event_date,
                            city=city,
                            category=category,
                            extra_fields=normalized_data_serializable
                        )
                        provider_backend.create_contextual_data(event, normalized_data_serializable)
                    except Exception as e:
                        logger.error(
                            f"[ERRO] Falha ao processar dados normalizados para integração '{integration.name}': {e}")

            except Exception as e:
                logger.error(f"[ERRO] Falha ao processar integração '{integration.name}': {e}")
                self.retry(exc=e)

        self.update_state(state='SUCCESS', meta={'status': 'Importação concluída com sucesso.'})
    except SoftTimeLimitExceeded:
        logger.error("[ERRO] Tempo limite excedido para a task.")
        self.update_state(state='FAILURE', meta={'status': 'Tempo limite excedido.'})
