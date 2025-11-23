from finance import db, app
from finance.models import Category


def init_database():
    with app.app_context():
        db.create_all()

        if Category.query.first() is None:
            add_default_categories()


def add_default_categories():

    categories = [
        {'name': 'housing', 'display_name': 'Жильё', 'icon': '🏠', 'order': 1},
        {'name': 'utilities', 'display_name': 'Коммунальные услуги', 'icon': '💡', 'order': 2},
        {'name': 'groceries', 'display_name': 'Продукты', 'icon': '🛒', 'order': 3},
        {'name': 'transport', 'display_name': 'Транспорт', 'icon': '🚗', 'order': 4},
        {'name': 'health', 'display_name': 'Здоровье', 'icon': '⚕️', 'order': 5},
        {'name': 'insurance', 'display_name': 'Страхование', 'icon': '🛡️', 'order': 6},

        {'name': 'restaurants', 'display_name': 'Рестораны и кафе', 'icon': '🍽️', 'order': 7},
        {'name': 'shopping', 'display_name': 'Покупки', 'icon': '🛍️', 'order': 8},
        {'name': 'entertainment', 'display_name': 'Развлечения', 'icon': '🎬', 'order': 9},
        {'name': 'sports', 'display_name': 'Спорт и фитнес', 'icon': '⚽', 'order': 10},
        {'name': 'beauty', 'display_name': 'Красота', 'icon': '💅', 'order': 11},

        {'name': 'phone', 'display_name': 'Связь', 'icon': '📱', 'order': 12},
        {'name': 'internet', 'display_name': 'Интернет', 'icon': '🌐', 'order': 13},
        {'name': 'subscriptions', 'display_name': 'Подписки', 'icon': '📺', 'order': 14},

        {'name': 'education', 'display_name': 'Образование', 'icon': '📚', 'order': 15},
        {'name': 'books', 'display_name': 'Книги', 'icon': '📖', 'order': 16},

        {'name': 'travel', 'display_name': 'Путешествия', 'icon': '✈️', 'order': 17},
        {'name': 'vacation', 'display_name': 'Отпуск', 'icon': '🏖️', 'order': 18},

        {'name': 'savings', 'display_name': 'Сбережения', 'icon': '💰', 'order': 19},
        {'name': 'investments', 'display_name': 'Инвестиции', 'icon': '📈', 'order': 20},
        {'name': 'debt', 'display_name': 'Долги и кредиты', 'icon': '💳', 'order': 21},

        {'name': 'gifts', 'display_name': 'Подарки', 'icon': '🎁', 'order': 22},
        {'name': 'pets', 'display_name': 'Питомцы', 'icon': '🐾', 'order': 23},
        {'name': 'charity', 'display_name': 'Благотворительность', 'icon': '❤️', 'order': 24},
        {'name': 'other', 'display_name': 'Прочее', 'icon': '📝', 'order': 25},
    ]

    with app.app_context():
        for cat_data in categories:
            category = Category(**cat_data)
            db.session.add(category)

        db.session.commit()


if __name__ == '__main__':
    init_database()
