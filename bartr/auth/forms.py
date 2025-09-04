from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from bartr.models import User
from flask_login import current_user

# Malaysia states and cities
MALAYSIA_CITIES = {
    'Johor': ['Johor Bahru', 'Batu Pahat', 'Muar', 'Kluang', 'Kulai', 'Segamat', 'Pontian', 'Tangkak', 'Mersing', 'Pasir Gudang', 'Iskandar Puteri'],
    'Kedah': ['Alor Setar', 'Sungai Petani', 'Kulim', 'Langkawi', 'Kubang Pasu', 'Baling', 'Yan', 'Pendang', 'Pokok Sena'],
    'Kelantan': ['Kota Bharu', 'Pasir Mas', 'Tumpat', 'Tanah Merah', 'Kuala Krai', 'Bachok', 'Gua Musang', 'Machang', 'Pasir Puteh'],
    'Melaka': ['Melaka City', 'Alor Gajah', 'Jasin', 'Masjid Tanah', 'Ayer Keroh', 'Bukit Katil'],
    'Negeri Sembilan': ['Seremban', 'Port Dickson', 'Nilai', 'Bahau', 'Tampin', 'Kuala Pilah', 'Rembau'],
    'Pahang': ['Kuantan', 'Temerloh', 'Bentong', 'Raub', 'Pekan', 'Cameron Highlands', 'Rompin', 'Maran'],
    'Perak': ['Ipoh', 'Taiping', 'Sitiawan', 'Teluk Intan', 'Batu Gajah', 'Kampar', 'Kuala Kangsar', 'Tanjung Malim'],
    'Perlis': ['Kangar', 'Arau', 'Padang Besar', 'Kuala Perlis'],
    'Pulau Pinang': ['George Town', 'Butterworth', 'Bukit Mertajam', 'Nibong Tebal', 'Balik Pulau', 'Air Itam', 'Bayan Lepas'],
    'Sabah': ['Kota Kinabalu', 'Sandakan', 'Tawau', 'Lahad Datu', 'Keningau', 'Beaufort', 'Kudat', 'Semporna'],
    'Sarawak': ['Kuching', 'Miri', 'Sibu', 'Bintulu', 'Limbang', 'Sarikei', 'Sri Aman', 'Kapit'],
    'Selangor': ['Shah Alam', 'Petaling Jaya', 'Subang Jaya', 'Klang', 'Ampang', 'Kajang', 'Cheras', 'Rawang', 'Sepang', 'Cyberjaya'],
    'Terengganu': ['Kuala Terengganu', 'Kemaman', 'Dungun', 'Marang', 'Besut', 'Hulu Terengganu', 'Setiu'],
    'Kuala Lumpur': ['Kuala Lumpur'],
    'Labuan': ['Victoria', 'Labuan'],
    'Putrajaya': ['Putrajaya']
}

# Malaysia states for dropdown
MALAYSIA_STATES = [('', 'Select State')] + [(state, state) for state in MALAYSIA_CITIES.keys()]

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    region = SelectField('State', choices=MALAYSIA_STATES, validators=[DataRequired()])
    city = SelectField('City', choices=[('', 'Select City')], validators=[DataRequired()])
    submit = SubmitField('Register')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        if self.region.data in MALAYSIA_CITIES:
            self.city.choices = [('', 'Select City')] + [(city, city) for city in MALAYSIA_CITIES[self.region.data]]

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

    def validate_city(self, city):
        if self.region.data not in MALAYSIA_CITIES:
            raise ValidationError('Please select a valid state first.')
        if city.data not in MALAYSIA_CITIES[self.region.data]:
            raise ValidationError('Please select a valid city for the selected state.')

class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile_number = StringField('Mobile Number', validators=[Length(max=20)])
    region = SelectField('State', choices=MALAYSIA_STATES, validators=[DataRequired()])
    city = SelectField('City', choices=[('', 'Select City')], validators=[DataRequired()])
    profile_photo = FileField('Profile Photo', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Save Changes')

    def __init__(self, *args, **kwargs):
        super(UpdateProfileForm, self).__init__(*args, **kwargs)
        if self.region.data in MALAYSIA_CITIES:
            self.city.choices = [('', 'Select City')] + [(city, city) for city in MALAYSIA_CITIES[self.region.data]]

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Please use a different email address.')

    def validate_city(self, city):
        if self.region.data not in MALAYSIA_CITIES:
            raise ValidationError('Please select a valid state first.')
        if city.data not in MALAYSIA_CITIES[self.region.data]:
            raise ValidationError('Please select a valid city for the selected state.')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6, message='Password must be at least 6 characters long')])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Change Password') 