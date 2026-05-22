from .models import SupportSession


def cart_info(request):
    cart = request.session.get('cart', {})
    count = sum(v['qty'] for v in cart.values())
    return {'cart_count': count}


def support_info(request):
    unread = 0
    if request.user.is_authenticated and request.user.is_staff:
        from .models import SupportMessage
        unread = SupportMessage.objects.filter(is_admin=False, is_read=False).count()
    return {'support_unread': unread}
