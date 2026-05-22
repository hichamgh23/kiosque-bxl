from decimal import Decimal
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.translation import gettext as _
from .models import Category, Product, Order, OrderItem, OrderMessage, SupportSession, SupportMessage, SiteSettings
from .forms import CheckoutForm
from .utils import send_telegram, generate_tracking_number

DELIVERY_FEE = Decimal('4.99')


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_staff):
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_dashboard')
    error = None
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username'), password=request.POST.get('password'))
        if user and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        error = 'Identifiant ou mot de passe incorrect.'
    return render(request, 'core/admin_login.html', {'error': error})


def admin_logout_view(request):
    logout(request)
    return redirect('admin_login')


# ── Helpers panier ──────────────────────────────────────────────────────────

def _get_cart(request):
    return request.session.get('cart', {})

def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True

def _cart_items(cart):
    items = []
    for pid, data in cart.items():
        try:
            p = Product.objects.get(pk=int(pid))
            items.append({'product': p, 'qty': data['qty'], 'subtotal': p.price * data['qty']})
        except Product.DoesNotExist:
            pass
    return items


# ── Pages publiques ─────────────────────────────────────────────────────────

from django.http import HttpResponse

def robots_txt(request):
    lines = [
        'User-agent: *',
        'Disallow: /admin-kiosque/',
        'Disallow: /i18n/',
        'Disallow: /messages/',
        'Disallow: /commande/confirmation/',
        'Disallow: /suivi/',
        'Allow: /',
        '',
        'Sitemap: https://' + request.get_host() + '/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')

def home(request):
    best_sellers = Product.objects.filter(featured=True, in_stock=True).select_related('category')[:8]
    categories   = Category.objects.all()
    return render(request, 'core/home.html', {
        'best_sellers': best_sellers,
        'categories':   categories,
    })

def kiosque(request):
    categories = Category.objects.prefetch_related('products').all()
    return render(request, 'core/kiosque.html', {'categories': categories})

def about(request):
    return render(request, 'core/about.html')

def how_it_works(request):
    return render(request, 'core/how_it_works.html')

def privacy(request):
    return render(request, 'core/privacy.html')

def cookies(request):
    return render(request, 'core/cookies.html')


# ── Panier ──────────────────────────────────────────────────────────────────

@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, in_stock=True)
    cart = _get_cart(request)
    key  = str(product_id)
    if key in cart:
        cart[key]['qty'] += 1
    else:
        cart[key] = {'qty': 1, 'name': product.name, 'price': str(product.price)}
    _save_cart(request, cart)
    return JsonResponse({'success': True, 'cart_count': sum(v['qty'] for v in cart.values())})

@require_POST
def remove_from_cart(request, product_id):
    cart = _get_cart(request)
    cart.pop(str(product_id), None)
    _save_cart(request, cart)
    return redirect('cart')

@require_POST
def update_cart(request, product_id):
    cart = _get_cart(request)
    key  = str(product_id)
    try:
        qty = int(request.POST.get('qty', 1))
    except (ValueError, TypeError):
        qty = 1
    qty = max(0, min(qty, 20))  # limite 0–20 par article
    if qty < 1:
        cart.pop(key, None)
    elif key in cart:
        cart[key]['qty'] = qty
    _save_cart(request, cart)
    return redirect('cart')

def cart_view(request):
    cart  = _get_cart(request)
    items = _cart_items(cart)
    total = sum(i['subtotal'] for i in items)
    return render(request, 'core/cart.html', {
        'items':        items,
        'total':        total,
        'delivery_fee': DELIVERY_FEE,
        'grand_total':  total + DELIVERY_FEE if items else 0,
    })


# ── Commande ────────────────────────────────────────────────────────────────

def checkout(request):
    if not SiteSettings.get().is_open:
        return redirect('kiosque')
    cart  = _get_cart(request)
    items = _cart_items(cart)
    if not items:
        return redirect('kiosque')
    total = sum(i['subtotal'] for i in items)

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.payment_method  = 'livraison'
            order.tracking_number = generate_tracking_number()
            order.save()
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    product_name=item['product'].name,
                    unit_price=item['product'].price,
                    quantity=item['qty'],
                )
            request.session['cart'] = {}
            request.session.modified = True

            # Message de bienvenue automatique
            OrderMessage.objects.create(
                order=order, is_admin=True,
                content=_('Bonjour %(name)s ! Votre commande #%(tracking)s a bien été reçue. Je la confirme très rapidement. N\'hésitez pas à m\'écrire ici si vous voulez ajouter quelque chose ou poser une question. 🛵') % {
                    'name': order.client_name,
                    'tracking': order.tracking_number,
                }
            )

            lines = '\n'.join(f"  {i['qty']}x {i['product'].name} — {i['subtotal']:.2f}EUR" for i in items)
            send_telegram(
                f"[COMMANDE #{order.pk}]\n"
                f"{order.client_name} | {order.phone}\n"
                f"{order.address}\n"
                f"{order.get_payment_method_display()}\n\n"
                f"{lines}\n\nTotal : {total:.2f}EUR"
            )
            return redirect('order_confirmation', order_id=order.pk)
    else:
        form = CheckoutForm()

    return render(request, 'core/checkout.html', {
        'form':         form,
        'items':        items,
        'total':        total,
        'delivery_fee': DELIVERY_FEE,
        'grand_total':  total + DELIVERY_FEE,
    })

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'core/order_confirmation.html', {'order': order})


def track_search(request):
    query = request.GET.get('q', '').strip()
    order = None
    error = None

    if query:
        if query.isdigit() and len(query) == 6:
            try:
                order = Order.objects.get(tracking_number=query)
                return redirect('track_order', order_id=order.pk)
            except Order.DoesNotExist:
                error = f"Aucune commande trouvée pour le numéro #{query}."
        else:
            error = "Entrez un numéro à 6 chiffres (ex : 847362)."

    return render(request, 'core/track_search.html', {
        'query': query, 'error': error,
    })


def track_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)

    STEPS = [
        ('en_attente',    _('En attente'),       '⏳', _('Commande reçue — je vais la confirmer rapidement.')),
        ('confirmee',     _('Confirmée'),        '✅', _('C\'est bon ! Je prépare vos articles.')),
        ('en_livraison',  _('En livraison'),     '🛵', _('Je suis en route vers chez vous !')),
        ('devant_maison', _('Devant chez vous'), '🔔', _('Je suis devant votre porte !')),
        ('livree',        _('Livrée'),           '🏠', _('Livraison effectuée. Merci et à bientôt !')),
    ]
    ORDER_FLOW = ['en_attente', 'confirmee', 'en_livraison', 'devant_maison', 'livree']

    if order.status == 'annulee':
        current_index = -1
    else:
        current_index = ORDER_FLOW.index(order.status) if order.status in ORDER_FLOW else 0

    return render(request, 'core/track_order.html', {
        'order':         order,
        'steps':         STEPS,
        'current_index': current_index,
        'is_cancelled':  order.status == 'annulee',
        'messages':      list(order.messages.all()),
    })


# ── Admin ───────────────────────────────────────────────────────────────────

@require_POST
def send_message(request, order_id):
    order   = get_object_or_404(Order, pk=order_id)
    content = request.POST.get('content', '').strip()[:500]
    if not content:
        return JsonResponse({'error': 'vide'}, status=400)

    is_admin = request.user.is_authenticated and request.user.is_staff
    msg = OrderMessage.objects.create(order=order, content=content, is_admin=is_admin)

    # Notif Telegram quand le client écrit
    if not is_admin:
        send_telegram(
            f"💬 <b>Message de {order.client_name}</b> (#{order.tracking_number})\n{content}"
        )

    return JsonResponse({
        'id':       msg.pk,
        'content':  msg.content,
        'is_admin': msg.is_admin,
        'time':     msg.created_at.strftime('%H:%M'),
    })


def order_status_json(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return JsonResponse({'status': order.status})


def get_messages(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    try:
        since = int(request.GET.get('since', 0))
    except (ValueError, TypeError):
        since = 0
    is_admin   = request.user.is_authenticated and request.user.is_staff
    other_role = 'client' if is_admin else 'admin'
    typing     = bool(cache.get(f'typing_{order_id}_{other_role}'))
    messages   = order.messages.filter(pk__gt=since).values('pk', 'content', 'is_admin', 'created_at')
    return JsonResponse({
        'messages': [
            {'id': m['pk'], 'content': m['content'], 'is_admin': m['is_admin'],
             'time': m['created_at'].strftime('%H:%M')}
            for m in messages
        ],
        'typing': typing,
    })


@require_POST
def set_typing(request, order_id):
    get_object_or_404(Order, pk=order_id)
    is_admin = request.user.is_authenticated and request.user.is_staff
    role     = 'admin' if is_admin else 'client'
    cache.set(f'typing_{order_id}_{role}', True, timeout=4)
    return JsonResponse({'ok': True})


@admin_required
@require_POST
def toggle_open(request):
    s = SiteSettings.get()
    s.is_open = not s.is_open
    s.save()
    return redirect('admin_dashboard')


@admin_required
def dashboard(request):
    status_filter = request.GET.get('status', '')
    orders = Order.objects.all()
    if status_filter:
        orders = orders.filter(status=status_filter)
    counts = {s: Order.objects.filter(status=s).count() for s, _ in Order.STATUS_CHOICES}
    counts['total'] = Order.objects.count()
    return render(request, 'core/dashboard.html', {
        'orders':         orders,
        'status_choices': Order.STATUS_CHOICES,
        'current_filter': status_filter,
        'counts':         counts,
        'pending_count':  counts.get('en_attente', 0),
        'settings':       SiteSettings.get(),
    })


@admin_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        if status in dict(Order.STATUS_CHOICES):
            order.status = status
            order.save()
        return redirect('admin_order_detail', order_id=order_id)
    return render(request, 'core/order_detail.html', {
        'order':          order,
        'status_choices': Order.STATUS_CHOICES,
        'messages':       list(order.messages.all()),
        'pending_count':  Order.objects.filter(status='en_attente').count(),
    })


# ── Support chat (widget public + admin) ─────────────────────────────────────

def _get_or_create_support_session(request):
    if not request.session.session_key:
        request.session.create()
    key = request.session.session_key
    session, _ = SupportSession.objects.get_or_create(session_key=key)
    return session


def support_page(request):
    session  = _get_or_create_support_session(request)
    msgs     = list(session.support_messages.all())
    return render(request, 'core/support_page.html', {
        'session':             session,
        'messages':            msgs,
        'hide_support_widget': True,
    })


@require_POST
def support_send(request):
    session = _get_or_create_support_session(request)
    content = request.POST.get('content', '').strip()
    name    = request.POST.get('visitor_name', '').strip()
    if not content:
        return JsonResponse({'error': 'vide'}, status=400)

    if name and session.visitor_name == 'Visiteur':
        session.visitor_name = name
        session.save(update_fields=['visitor_name'])

    is_admin = request.user.is_authenticated and request.user.is_staff
    msg = SupportMessage.objects.create(session=session, content=content, is_admin=is_admin)

    if not is_admin:
        send_telegram(
            f"💬 <b>Support — {session.visitor_name}</b>\n{content}"
        )

    return JsonResponse({
        'id':       msg.pk,
        'content':  msg.content,
        'is_admin': msg.is_admin,
        'time':     msg.created_at.strftime('%H:%M'),
    })


def support_poll(request):
    session = _get_or_create_support_session(request)
    try:
        since = int(request.GET.get('since', 0))
    except (ValueError, TypeError):
        since = 0
    msgs   = session.support_messages.filter(pk__gt=since).values('pk', 'content', 'is_admin', 'created_at')
    typing = bool(cache.get(f'typing_support_{session.pk}_admin'))
    session.support_messages.filter(is_admin=True, is_read=False).update(is_read=True)
    return JsonResponse({
        'messages': [
            {'id': m['pk'], 'content': m['content'], 'is_admin': m['is_admin'],
             'time': m['created_at'].strftime('%H:%M')}
            for m in msgs
        ],
        'typing': typing,
    })


@require_POST
def support_typing(request):
    session = _get_or_create_support_session(request)
    cache.set(f'typing_support_{session.pk}_client', True, timeout=4)
    return JsonResponse({'ok': True})


@admin_required
def admin_support(request):
    sessions = SupportSession.objects.prefetch_related('support_messages').all()
    return render(request, 'core/admin_support.html', {
        'sessions':      sessions,
        'pending_count': Order.objects.filter(status='en_attente').count(),
    })


@admin_required
@require_POST
def admin_support_send(request, session_id):
    session = get_object_or_404(SupportSession, pk=session_id)
    content = request.POST.get('content', '').strip()[:500]
    if not content:
        return JsonResponse({'error': 'vide'}, status=400)
    msg = SupportMessage.objects.create(session=session, content=content, is_admin=True)
    return JsonResponse({
        'id':       msg.pk,
        'content':  msg.content,
        'is_admin': msg.is_admin,
        'time':     msg.created_at.strftime('%H:%M'),
    })


@admin_required
def admin_support_poll(request, session_id):
    session = get_object_or_404(SupportSession, pk=session_id)
    try:
        since = int(request.GET.get('since', 0))
    except (ValueError, TypeError):
        since = 0
    msgs   = session.support_messages.filter(pk__gt=since).values('pk', 'content', 'is_admin', 'created_at')
    typing = bool(cache.get(f'typing_support_{session_id}_client'))
    session.support_messages.filter(is_admin=False, is_read=False).update(is_read=True)
    return JsonResponse({
        'messages': [
            {'id': m['pk'], 'content': m['content'], 'is_admin': m['is_admin'],
             'time': m['created_at'].strftime('%H:%M')}
            for m in msgs
        ],
        'typing': typing,
    })


@admin_required
@require_POST
def admin_support_typing(request, session_id):
    get_object_or_404(SupportSession, pk=session_id)
    cache.set(f'typing_support_{session_id}_admin', True, timeout=4)
    return JsonResponse({'ok': True})
