from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FloatField, IntegerField, BooleanField, SelectField, PasswordField, HiddenField
from wtforms.validators import DataRequired, Length, Email, NumberRange, Optional
from wtforms.widgets import TextArea


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class ProductForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description')
    price_inr = FloatField('Price (INR)', validators=[DataRequired(), NumberRange(min=0.01)])
    active = BooleanField('Active', default=True)
    stock = IntegerField('Stock', validators=[Optional()], default=None)
    featured = BooleanField('Featured', default=False)
    is_hot_product = BooleanField('Hot Product', default=False)
    discount_override = FloatField(
        'Discount Override (%)', 
        validators=[Optional(), NumberRange(min=0, max=100)], 
        default=None
    )
    per_product_discount = FloatField(
        'Per Product Discount (%)', 
        validators=[Optional(), NumberRange(min=0, max=100)], 
        default=None
    )
    # For image uploads, we'll handle these in the view since WTForms doesn't handle multiple files well
    # Images will be handled separately in the template and view


class LeadForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    telegram_username = StringField('Telegram Username', validators=[Optional(), Length(max=50)])
    message = TextAreaField('Message', validators=[Optional()])
    # product_ids will be passed as hidden field from cart


class SiteSettingsForm(FlaskForm):
    store_name = StringField('Store Name', validators=[DataRequired(), Length(max=100)])
    banner_text = StringField('Banner Text', validators=[DataRequired(), Length(max=200)])
    global_discount_percent = FloatField(
        'Global Discount (%)', 
        validators=[DataRequired(), NumberRange(min=0, max=100)]
    )
    theme_name = SelectField(
        'Theme',
        choices=[('light', 'Light'), ('dark', 'Dark')],
        validators=[DataRequired()]
    )
    contact_email = StringField('Contact Email', validators=[Optional(), Email(), Length(max=100)])
    contact_phone = StringField('Contact Phone', validators=[Optional(), Length(max=20)])
    contact_address = TextAreaField('Contact Address', widget=TextArea())
    telegram_bot_token = StringField('Telegram Bot Token', validators=[Optional(), Length(max=200)])
    admin_telegram_chat_id = StringField('Admin Telegram Chat ID', validators=[Optional(), Length(max=50)])
    privacy_policy = TextAreaField('Privacy Policy', widget=TextArea())
    terms = TextAreaField('Terms', widget=TextArea())
    about = TextAreaField('About', widget=TextArea())


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    featured = BooleanField('Featured', default=False)


class AdminPageForm(FlaskForm):
    content = TextAreaField('Content', widget=TextArea(), validators=[DataRequired()])