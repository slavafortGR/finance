from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from finance import app, db
from finance.models import User, Income, Expense, Category, CategoryUsage
from datetime import datetime, date
from sqlalchemy import func, extract


@app.route('/')
@login_required
def index():
    current_date = date.today()
    year = request.args.get('year', current_date.year, type=int)
    month = request.args.get('month', current_date.month, type=int)

    income = Income.query.filter_by(
        user_id=current_user.id,
        year=year,
        month=month
    ).first()

    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        extract('year', Expense.date) == year,
        extract('month', Expense.date) == month
    ).all()

    expenses_by_category = db.session.query(
        Category,
        func.sum(Expense.amount).label('total')
    ).join(Expense).filter(
        Expense.user_id == current_user.id,
        extract('year', Expense.date) == year,
        extract('month', Expense.date) == month
    ).group_by(Category).order_by(func.sum(Expense.amount).desc()).all()

    # Подсчитываем итоги
    total_income = income.total if income else 0
    total_expenses = sum(exp.amount for exp in expenses)
    balance = total_income - total_expenses

    return render_template('dashboard.html',
                           income=income,
                           total_income=total_income,
                           total_expenses=total_expenses,
                           balance=balance,
                           expenses=expenses,
                           expenses_by_category=expenses_by_category,
                           year=year,
                           month=month)


@app.route('/income', methods=['GET', 'POST'])
@login_required
def income():
    if request.method == 'POST':
        year = int(request.form.get('year'))
        month = int(request.form.get('month'))
        main_income = int(request.form.get('main_income', 0))
        additional_income = int(request.form.get('additional_income', 0))

        income_record = Income.query.filter_by(
            user_id=current_user.id,
            year=year,
            month=month
        ).first()

        if income_record:
            income_record.main_income = main_income
            income_record.additional_income = additional_income
            income_record.updated_at = datetime.utcnow()
        else:
            income_record = Income(
                user_id=current_user.id,
                year=year,
                month=month,
                main_income=main_income,
                additional_income=additional_income
            )
            db.session.add(income_record)

        db.session.commit()
        flash('Доход сохранен', 'success')
        return redirect(url_for('index'))

    current_date = date.today()
    year = request.args.get('year', current_date.year, type=int)
    month = request.args.get('month', current_date.month, type=int)

    income_record = Income.query.filter_by(
        user_id=current_user.id,
        year=year,
        month=month
    ).first()

    return render_template('income.html',
                           income=income_record,
                           year=year,
                           month=month)


@app.route('/expenses')
@login_required
def expenses():
    page = request.args.get('page', 1, type=int)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    category_id = request.args.get('category_id', type=int)

    query = Expense.query.filter_by(user_id=current_user.id)

    if year:
        query = query.filter(extract('year', Expense.date) == year)
    if month:
        query = query.filter(extract('month', Expense.date) == month)
    if category_id:
        query = query.filter_by(category_id=category_id)

    expenses = query.order_by(Expense.date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    categories = Category.query.order_by(Category.order).all()

    return render_template('expenses.html',
                           expenses=expenses,
                           categories=categories)


@app.route('/expense/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        category_id = int(request.form.get('category_id'))
        amount = int(request.form.get('amount'))
        expense_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        comment = request.form.get('comment', '').strip()

        expense = Expense(
            user_id=current_user.id,
            category_id=category_id,
            amount=amount,
            date=expense_date,
            comment=comment if comment else None
        )
        db.session.add(expense)

        usage = CategoryUsage.query.filter_by(
            user_id=current_user.id,
            category_id=category_id
        ).first()

        if usage:
            usage.usage_count += 1
            usage.last_used = datetime.utcnow()
        else:
            usage = CategoryUsage(
                user_id=current_user.id,
                category_id=category_id,
                usage_count=1
            )
            db.session.add(usage)

        db.session.commit()
        flash('Расход добавлен', 'success')
        return redirect(url_for('index'))


    popular_categories = db.session.query(Category).outerjoin(
        CategoryUsage,
        (CategoryUsage.category_id == Category.id) &
        (CategoryUsage.user_id == current_user.id)
    ).order_by(
        CategoryUsage.usage_count.desc().nullslast(),
        Category.order
    ).all()

    return render_template('add_expense.html',
                           categories=popular_categories,
                           today=date.today())


@app.route('/expense/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)

    if expense.user_id != current_user.id:
        flash('Нет доступа', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        expense.category_id = int(request.form.get('category_id'))
        expense.amount = int(request.form.get('amount'))
        expense.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        expense.comment = request.form.get('comment', '').strip() or None
        expense.updated_at = datetime.utcnow()

        db.session.commit()
        flash('Расход обновлен', 'success')
        return redirect(url_for('expenses'))

    categories = Category.query.order_by(Category.order).all()
    return render_template('edit_expense.html',
                           expense=expense,
                           categories=categories)


@app.route('/expense/<int:expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)

    if expense.user_id != current_user.id:
        flash('Нет доступа', 'error')
        return redirect(url_for('index'))

    db.session.delete(expense)
    db.session.commit()
    flash('Расход удален', 'success')
    return redirect(url_for('expenses'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован', 'error')
            return redirect(url_for('register'))

        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Регистрация успешна! Войдите в систему.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Неверный email или пароль', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Выход пользователя"""
    logout_user()
    return redirect(url_for('login'))


@app.route('/api/categories')
@login_required
def api_categories():
    categories = Category.query.order_by(Category.order).all()
    return jsonify([{
        'id': cat.id,
        'name': cat.name,
        'display_name': cat.display_name,
        'icon': cat.icon
    } for cat in categories])


@app.route('/api/stats/<int:year>/<int:month>')
@login_required
def api_stats(year, month):
    income = Income.query.filter_by(
        user_id=current_user.id,
        year=year,
        month=month
    ).first()

    expenses_by_category = db.session.query(
        Category.display_name,
        Category.icon,
        func.sum(Expense.amount).label('total')
    ).join(Expense).filter(
        Expense.user_id == current_user.id,
        extract('year', Expense.date) == year,
        extract('month', Expense.date) == month
    ).group_by(Category.display_name, Category.icon).all()

    total_income = income.total if income else 0
    total_expenses = sum(item.total for item in expenses_by_category)

    return jsonify({
        'income': total_income,
        'expenses': total_expenses,
        'balance': total_income - total_expenses,
        'categories': [{
            'name': item.display_name,
            'icon': item.icon,
            'amount': item.total
        } for item in expenses_by_category]
    })
