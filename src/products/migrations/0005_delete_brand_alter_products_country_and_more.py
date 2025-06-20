# Generated by Django 5.0 on 2025-06-18 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0004_brand_country_products_brand_products_season_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Brand',
        ),
        migrations.AlterField(
            model_name='products',
            name='country',
            field=models.CharField(choices=[('it', 'Италия'), ('de', 'Германия'), ('pt', 'Португалия'), ('es', 'Испания'), ('fr', 'Франция'), ('uk', 'Великобритания'), ('tr', 'Турция'), ('cn', 'Китай'), ('vn', 'Вьетнам'), ('in', 'Индия'), ('id', 'Индонезия'), ('jp', 'Япония'), ('kr', 'Южная Корея'), ('us', 'США'), ('br', 'Бразилия'), ('mx', 'Мексика'), ('ru', 'Россия'), ('by', 'Беларусь'), ('za', 'Южная Африка'), ('au', 'Австралия')], default='ru', max_length=32, verbose_name='Страна производитель'),
        ),
        migrations.RemoveField(
            model_name='products',
            name='params',
        ),
        migrations.AddField(
            model_name='products',
            name='sole_material',
            field=models.CharField(choices=[('tpr', 'Термопластичная резина (TPR)'), ('pu', 'Полиуретан (PU)'), ('eva', 'Этиленвинилацетат (EVA)'), ('rubber', 'Натуральный каучук/резина'), ('tpu', 'Термополиуретан (TPU)'), ('pvc', 'Поливинилхлорид (PVC)'), ('phylon', 'Файлон (Phylon)'), ('phylite', 'Файлайт (Phylite)'), ('compressed_rubber', 'Прессованная резина'), ('carbon', 'Карбоновая подошва'), ('microcellular', 'Микропористая резина'), ('crepe', 'Креповая подошва'), ('leather', 'Кожаная подошва'), ('combination', 'Комбинированная подошва')], default='leather', max_length=20, verbose_name='Материал подошвы'),
        ),
        migrations.AlterField(
            model_name='products',
            name='brand',
            field=models.CharField(choices=[('nike', 'Nike'), ('adidas', 'Adidas'), ('puma', 'Puma'), ('reebok', 'Reebok'), ('new_balance', 'New Balance'), ('asics', 'ASICS'), ('under_armour', 'Under Armour'), ('skechers', 'Skechers'), ('gucci', 'Gucci'), ('prada', 'Prada'), ('louis_vuitton', 'Louis Vuitton'), ('balenciaga', 'Balenciaga'), ('dior', 'Dior'), ('vans', 'Vans'), ('converse', 'Converse'), ('timberland', 'Timberland'), ('dr_martens', 'Dr. Martens'), ('salomon', 'Salomon'), ('merrell', 'Merrell'), ('columbia', 'Columbia'), ('the_north_face', 'The North Face'), ('ralf_ringer', 'Ralf Ringer'), ('ecco', 'ECCO'), ('bugatti', 'Bugatti'), ('carlo_pazolini', 'Carlo Pazolini'), ('kapitoshka', 'Капитошка'), ('kotofey', 'Котофей'), ('antilopa', 'Антилопа'), ('bartek', 'Bartek')], default='nike', max_length=120, verbose_name='Брэнд'),
        ),
        migrations.AlterField(
            model_name='products',
            name='upper_material',
            field=models.CharField(choices=[('leather', 'Натуральная кожа'), ('suede', 'Замша'), ('nubuck', 'Нубук'), ('textile', 'Текстиль'), ('mesh', 'Сетка (дышащий материал)'), ('synthetic', 'Искусственная кожа'), ('knit', 'Вязаный материал'), ('thermo', 'Термополиуретан (TPU)'), ('rubber', 'Резина/каучук'), ('pu', 'Полиуретан (PU)'), ('eva', 'Этиленвинилацетат (EVA)'), ('neoprene', 'Неопрен'), ('goretex', 'Мембрана Gore-Tex'), ('elastic', 'Эластичные материалы'), ('combination', 'Комбинированные материалы')], default='leather', max_length=20, verbose_name='Материал верха'),
        ),
        migrations.DeleteModel(
            name='Country',
        ),
    ]
