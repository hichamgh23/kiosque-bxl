from .models import SupportSession, SiteSettings


def cart_info(request):
    cart = request.session.get('cart', {})
    count = sum(v['qty'] for v in cart.values())
    return {'cart_count': count}


def site_settings(request):
    try:
        s = SiteSettings.get()
        return {'site_is_open': s.is_open, 'site_opening_hours': s.opening_hours, 'site_closed_msg': s.closed_msg}
    except Exception:
        return {'site_is_open': True, 'site_opening_hours': '', 'site_closed_msg': ''}


def support_info(request):
    unread = 0
    if request.user.is_authenticated and request.user.is_staff:
        from .models import SupportMessage
        unread = SupportMessage.objects.filter(is_admin=False, is_read=False).count()
    return {'support_unread': unread}
