from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, IntegerField, SubmitField, FloatField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class ItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description (optional)', validators=[Optional(), Length(max=1000)])
    condition = SelectField('Condition', choices=[
        ('brand_new', 'Brand new'),
        ('like_new', 'Like new'),
        ('lightly_used', 'Lightly used'),
        ('well_used', 'Well used'),
        ('heavily_used', 'Heavily used')
    ], validators=[DataRequired()])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    estimated_value = FloatField('Estimated Value (RM)', validators=[Optional(), NumberRange(min=0, message='Value must be positive')])
    photos = MultipleFileField('Photos', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Submit')

class TradeForm(FlaskForm):
    offered_items = SelectMultipleField('Select Items to Offer', coerce=int, validators=[DataRequired()])
    message = TextAreaField('Message (optional)', validators=[Length(max=500)])
    submit = SubmitField('Propose Trade')

class MessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[Optional(), Length(max=500)])
    images = MultipleFileField('Images', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Send')

class ReviewForm(FlaskForm):
    rating = IntegerField('Rating (1-5)', validators=[
        DataRequired(),
        NumberRange(min=1, max=5, message='Rating must be between 1 and 5')
    ])
    comment = TextAreaField('Comment', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Submit Review')

class FlagForm(FlaskForm):
    violation_type = SelectField('Violation Type', choices=[
        ('inappropriate_content', 'Inappropriate Content'),
        ('spam', 'Spam'),
        ('fake_item', 'Fake Item'),
        ('misleading_description', 'Misleading Description'),
        ('offensive_language', 'Offensive Language'),
        ('harassment', 'Harassment'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    reason = TextAreaField('Additional Details (Optional)', validators=[
        Length(max=500, message='Please keep additional details under 500 characters.')
    ])
    submit = SubmitField('Submit Report') 