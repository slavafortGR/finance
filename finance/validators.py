from wtforms.validators import ValidationError
from datetime import date


class NotFutureDate:
    def __init__(self, message=None):
        if not message:
            message = 'Date cannot be in the future'
        self.message = message

    def __call__(self, form, field):
        if field.data:
            if isinstance(field.data, str):
                try:
                    year, month, day = field.data.split('-')
                    input_date = date(int(year), int(month), int(day))
                except (ValueError, AttributeError):
                    raise ValidationError('Invalid date format')
            elif isinstance(field.data, date):
                input_date = field.data
            else:
                raise ValidationError('Invalid date type')

            today = date.today()
            if input_date > today:
                raise ValidationError(self.message)
