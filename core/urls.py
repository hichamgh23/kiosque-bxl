from django.urls import path
from . import views

urlpatterns = [
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('', views.home, name='home'),
    path('confidentialite/', views.privacy, name='privacy'),
    path('cookies/', views.cookies, name='cookies'),
    path('kiosque/', views.kiosque, name='kiosque'),
    path('a-propos/', views.about, name='about'),
    path('comment-ca-marche/', views.how_it_works, name='how_it_works'),
    # Panier
    path('panier/', views.cart_view, name='cart'),
    path('panier/ajouter/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('panier/retirer/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('panier/modifier/<int:product_id>/', views.update_cart, name='update_cart'),
    # Commande
    path('commande/', views.checkout, name='checkout'),
    path('commande/confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('suivi/', views.track_search, name='track_search'),
    path('suivi/<int:order_id>/', views.track_order, name='track_order'),
    # Chat commande
    path('messages/<int:order_id>/send/', views.send_message, name='send_message'),
    path('messages/<int:order_id>/get/', views.get_messages, name='get_messages'),
    path('messages/<int:order_id>/typing/', views.set_typing, name='set_typing'),
    path('commande/<int:order_id>/status/', views.order_status_json, name='order_status_json'),
    # Support chat (public)
    path('support/', views.support_page, name='support_page'),
    path('support/send/', views.support_send, name='support_send'),
    path('support/poll/', views.support_poll, name='support_poll'),
    path('support/typing/', views.support_typing, name='support_typing'),
    # ── Espace admin dédié ────────────────────────────────────────────────────
    path('admin-kiosque/login/', views.admin_login_view, name='admin_login'),
    path('admin-kiosque/logout/', views.admin_logout_view, name='admin_logout'),
    path('admin-kiosque/', views.dashboard, name='admin_dashboard'),
    path('admin-kiosque/commande/<int:order_id>/', views.order_detail, name='admin_order_detail'),
    path('admin-kiosque/support/', views.admin_support, name='admin_support'),
    path('admin-kiosque/support/<int:session_id>/send/', views.admin_support_send, name='admin_support_send'),
    path('admin-kiosque/support/<int:session_id>/poll/', views.admin_support_poll, name='admin_support_poll'),
    path('admin-kiosque/support/<int:session_id>/typing/', views.admin_support_typing, name='admin_support_typing'),
    # Anciens liens dashboard (redirigent vers le nouvel espace)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/<int:order_id>/', views.order_detail, name='order_detail'),
]
