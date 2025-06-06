from dj_rql.filter_cls import AutoRQLFilterClass

from integrations.models import ContextualEvent, ContextualData


class ContextualEventFilterClass(AutoRQLFilterClass):
    """
    Filter class for the Reservation model.
    """
    MODEL = ContextualEvent


class ContextualDataFilterClass(AutoRQLFilterClass):
    """
    Filter class for the ContextualData model.
    """
    MODEL = ContextualData
