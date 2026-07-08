from .models import User


def resolve_acting_user(request, param_name, role=None):
    """Возвращает пользователя, от имени которого выполняется действие.

    Telegram-бот обращается к API под одной служебной учётной записью
    (см. bot/api_client.py), поэтому для операций, инициированных реальным
    пользователем через Telegram, доверенный (is_staff) клиент явно
    передаёт его id в параметре param_name. Подмена разрешена только
    staff-клиентам API — обычные пользователи всегда действуют от своего
    имени (request.user), параметр для них игнорируется.
    """
    actor = request.user
    if actor.is_staff:
        acting_id = request.data.get(param_name)
        if acting_id:
            qs = User.objects.filter(pk=acting_id)
            if role:
                qs = qs.filter(role=role)
            acting_user = qs.first()
            if acting_user:
                return acting_user
    return actor
