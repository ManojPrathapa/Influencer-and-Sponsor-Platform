from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, SelectField, DateField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=15)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    user_role = SelectField('Role', choices=[('admin', 'Admin'), ('sponsor', 'Sponsor'), ('influencer', 'Influencer')], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')

class CampaignForm(FlaskForm):
    title = StringField('Campaign Title', validators=[DataRequired()])
    campaign_description = TextAreaField('Description', validators=[DataRequired()])
    start = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    campaign_budget = FloatField('Budget', validators=[DataRequired()])
    visibility = SelectField('Visibility', choices=[('public', 'Public'), ('private', 'Private')], validators=[DataRequired()])
    campaign_goals = TextAreaField('Goals', validators=[DataRequired()])
    submit = SubmitField('Create Campaign')

class AdRequestForm(FlaskForm):
    request_content = TextAreaField('Content', validators=[DataRequired()])
    payment = FloatField('Payment Amount', validators=[DataRequired()])
    submit = SubmitField('Submit Ad Request')

class UpdateSponsorForm(FlaskForm):
    company = StringField('Company Name', validators=[DataRequired()])
    sector = StringField('Industry', validators=[DataRequired()])
    company_description = TextAreaField('Company Description', validators=[DataRequired()])
    submit = SubmitField('Update Profile')

class UpdateInfluencerForm(FlaskForm):
    influencer_name = StringField('Influencer Name', validators=[DataRequired()])
    specialization = StringField('Specialization', validators=[DataRequired()])
    audience_size = FloatField('Audience Size', validators=[DataRequired()])
    interests = TextAreaField('Interests', validators=[DataRequired()])
    submit = SubmitField('Update Profile')
