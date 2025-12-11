from finance import db, app
from finance.models import Category


def init_database():
    with app.app_context():
        db.create_all()

        if Category.query.first() is None:
            add_default_categories()


def add_default_categories():

    categories = [
        {'name': 'housing', 'display_name': 'Housing', 'icon': '🏠', 'order': 1},
        {'name': 'utilities', 'display_name': 'Utilities', 'icon': '💡', 'order': 2},
        {'name': 'groceries', 'display_name': 'Groceries', 'icon': '🛒', 'order': 3},
        {'name': 'transport', 'display_name': 'Transport', 'icon': '🚗', 'order': 4},
        {'name': 'health', 'display_name': 'Health', 'icon': '⚕️', 'order': 5},
        {'name': 'insurance', 'display_name': 'Insurance', 'icon': '🛡️', 'order': 6},

        {'name': 'restaurants', 'display_name': 'Restaurants', 'icon': '🍽️', 'order': 7},
        {'name': 'shopping', 'display_name': 'Shopping', 'icon': '🛍️', 'order': 8},
        {'name': 'entertainment', 'display_name': 'Entertainment', 'icon': '🎬', 'order': 9},
        {'name': 'sports', 'display_name': 'Sports & Fitness', 'icon': '⚽', 'order': 10},
        {'name': 'beauty', 'display_name': 'Beauty', 'icon': '💅', 'order': 11},

        {'name': 'phone', 'display_name': 'Phone', 'icon': '📱', 'order': 12},
        {'name': 'internet', 'display_name': 'Internet', 'icon': '🌐', 'order': 13},
        {'name': 'subscriptions', 'display_name': 'Subscriptions', 'icon': '📺', 'order': 14},

        {'name': 'education', 'display_name': 'Education', 'icon': '📚', 'order': 15},
        {'name': 'books', 'display_name': 'Books', 'icon': '📖', 'order': 16},

        {'name': 'travel', 'display_name': 'Travel', 'icon': '✈️', 'order': 17},
        {'name': 'vacation', 'display_name': 'Vacation', 'icon': '🏖️', 'order': 18},

        {'name': 'savings', 'display_name': 'Savings', 'icon': '💰', 'order': 19},
        {'name': 'investments', 'display_name': 'Investments', 'icon': '📈', 'order': 20},
        {'name': 'debt', 'display_name': 'Debt & Credits', 'icon': '💳', 'order': 21},

        {'name': 'gifts', 'display_name': 'Gifts', 'icon': '🎁', 'order': 22},
        {'name': 'pets', 'display_name': 'Pets', 'icon': '🐾', 'order': 23},
        {'name': 'charity', 'display_name': 'Charity', 'icon': '❤️', 'order': 24},
        {'name': 'other', 'display_name': 'Other', 'icon': '📝', 'order': 25},
    ]

    with app.app_context():
        for cat_data in categories:
            category = Category(**cat_data)
            db.session.add(category)

        db.session.commit()


if __name__ == '__main__':
    init_database()
