from django.core.management.base import BaseCommand
from core.models import Category, Product


DATA = [
    {
        'name': 'Snacks salés',
        'slug': 'snacks-sales',
        'icon': '🥨',
        'order': 1,
        'products': [
            ('Chips Lays Nature',       'Sachet 150g',              '1.50', '🥔', True),
            ('Chips Lays Paprika',      'Sachet 150g',              '1.50', '🌶️', True),
            ('Cacahuètes grillées',     'Sachet 200g',              '1.80', '🥜', True),
            ('Crackers TUC',            'Boîte 100g',               '1.20', '🫘', True),
            ('Biscuits apéro Mix',      'Sachet 250g',              '2.00', '🧂', True),
            ('Chips Pringles Original', 'Tube 165g',                '2.50', '🍟', True),
            ('Popcorn salé',            'Sachet 80g',               '1.00', '🍿', True),
            ('Olives vertes',           'Bocal 180g',               '1.80', '🫒', False),
        ],
    },
    {
        'name': 'Snacks sucrés',
        'slug': 'snacks-sucres',
        'icon': '🍫',
        'order': 2,
        'products': [
            ('Kinder Bueno',            '2 barres 43g',             '1.20', '🍫', True),
            ('Milka Oreo',              'Tablette 100g',            '1.80', '🍪', True),
            ('Haribo Goldbears',        'Sachet 100g',              '1.00', '🐻', True),
            ('Lion Bar',                '1 barre 42g',              '0.90', '🦁', True),
            ('Oreo Original',           'Paquet 154g',              '1.50', '🍪', True),
            ('Nutella B-ready',         'Paquet 6 pièces',          '2.20', '🥜', True),
            ('Chupa Chups',             '5 sucettes assorties',     '1.50', '🍭', True),
            ('Stroopwafels',            'Paquet 8 gaufres',         '2.00', '🧇', True),
        ],
    },
    {
        'name': 'Boissons',
        'slug': 'boissons',
        'icon': '🥤',
        'order': 3,
        'products': [
            ('Coca-Cola',               'Canette 33cl',             '1.20', '🥤', True),
            ('Fanta Orange',            'Canette 33cl',             '1.20', '🍊', True),
            ('Sprite',                  'Canette 33cl',             '1.20', '💧', True),
            ('Red Bull',                'Canette 25cl',             '2.00', '🐂', True),
            ('Monster Energy',          'Canette 50cl',             '2.50', '🟢', True),
            ('Eau Spa Reine',           'Bouteille 50cl',           '0.80', '💧', True),
            ('Lipton Ice Tea Pêche',    'Bouteille 50cl',           '1.50', '🍑', True),
            ('Jus d\'orange Minute Maid', 'Bouteille 33cl',         '1.50', '🍊', True),
            ('Tropico',                 'Canette 33cl',             '1.20', '🌴', True),
        ],
    },
    {
        'name': 'Hygiène & maison',
        'slug': 'hygiene',
        'icon': '🧴',
        'order': 4,
        'products': [
            ('Papier toilette',         'Rouleau x4',               '2.50', '🧻', True),
            ('Savon Dove',              'Pain 100g',                '1.50', '🫧', True),
            ('Déodorant Axe',           'Spray 150ml',              '3.50', '💨', True),
            ('Lingettes humides',       'Paquet 20 pièces',         '1.80', '🧼', True),
            ('Gel hydroalcoolique',     'Flacon 100ml',             '2.00', '🧴', True),
            ('Mouchoirs Kleenex',       'Paquet 10 pièces',         '1.00', '🤧', True),
            ('Préservatifs Durex',      'Boîte x3',                 '3.00', '❤️', True),
        ],
    },
]


class Command(BaseCommand):
    help = 'Ajoute des catégories et produits de démonstration'

    def handle(self, *args, **kwargs):
        created_cats = 0
        created_prods = 0

        for cat_data in DATA:
            cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'icon': cat_data['icon'],
                    'order': cat_data['order'],
                }
            )
            if created:
                created_cats += 1
                self.stdout.write(f"  + Categorie : {cat_data['name']}")

            for name, desc, price, emoji, in_stock in cat_data['products']:
                _, created = Product.objects.get_or_create(
                    name=name,
                    category=cat,
                    defaults={
                        'description': desc,
                        'price': price,
                        'emoji': emoji,
                        'in_stock': in_stock,
                    }
                )
                if created:
                    created_prods += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n{created_cats} catégories et {created_prods} produits ajoutés.'
        ))
