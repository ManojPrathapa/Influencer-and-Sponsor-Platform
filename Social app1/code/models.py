from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    bio = db.Column(db.String(255), nullable=True)
    linked_campaigns = db.relationship('Campaign', secondary='campaign_influencer', backref=db.backref('associated_influencers', lazy='dynamic'))

    def get_id(self):
        return self.user_id

class Sponsor(db.Model):
    sponsor_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    company = db.Column(db.String(120), nullable=True)
    sector = db.Column(db.String(120), nullable=True)
    sponsor_budget = db.Column(db.Float, nullable=True)
    company_description = db.Column(db.Text, nullable=True)  # New field for description

    user = db.relationship('User', backref=db.backref('sponsors', lazy=True))

    def __repr__(self):
        return f"Sponsor('{self.company}')"

class Influencer(db.Model):
    influencer_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    influencer_name = db.Column(db.String(120), nullable=True)
    genre = db.Column(db.String(120), nullable=True)
    specialization = db.Column(db.String(120), nullable=True)
    audience_size = db.Column(db.Float, nullable=True)
    interests = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f"Influencer('{self.influencer_name}', '{self.genre}')"

class Campaign(db.Model):
    campaign_id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.sponsor_id'))
    title = db.Column(db.String(100), nullable=False)
    campaign_description = db.Column(db.Text, nullable=False)
    start = db.Column(db.Date, nullable=False)  # Changed from DateTime to Date
    end = db.Column(db.Date, nullable=False)    # Changed from DateTime to Date
    campaign_budget = db.Column(db.Float, nullable=False)
    visibility = db.Column(db.String(50), nullable=False)
    campaign_goals = db.Column(db.Text, nullable=True)

    sponsor = db.relationship('Sponsor', backref=db.backref('campaigns_list', lazy=True))

class CampaignInfluencer(db.Model):
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.campaign_id'), primary_key=True)
    influencer_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True)

    def __repr__(self):
        return f"CampaignInfluencer(campaign_id={self.campaign_id}, influencer_id={self.influencer_id})"

class AdRequest(db.Model):
    request_id = db.Column(db.Integer, primary_key=True)
    request_content = db.Column(db.Text)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.campaign_id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    request_status = db.Column(db.String(50), default='Pending')
    payment_amount = db.Column(db.Float)
    campaign = db.relationship('Campaign', backref=db.backref('ad_requests_list', lazy=True))
    influencer = db.relationship('User', backref=db.backref('ad_requests_list', lazy=True))
