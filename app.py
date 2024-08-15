from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from models import db, User, Sponsor, Influencer, Campaign, CampaignInfluencer, AdRequest
from forms import LoginForm, RegisterForm, CampaignForm, AdRequestForm, UpdateSponsorForm
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database, password hashing, and login management
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    """Load user from database by ID."""
    return User.query.get(user_id)

@app.before_request
def custom_middleware():
    """Restrict admin pages to users with admin role only."""
    if request.path.startswith('/admin') and current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('index'))


@app.route('/')
def index():
    """Render the homepage."""
    return render_template('base.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for(f'{user.role}_dashboard'))
        flash('Invalid credentials!', 'danger')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle new user registration."""
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_pw, role=form.user_role.data)
        db.session.add(new_user)
        db.session.commit()

        if form.user_role.data == 'sponsor':
            db.session.add(Sponsor(user_id=new_user.user_id))
        elif form.user_role.data == 'influencer':
            db.session.add(Influencer(user_id=new_user.user_id))
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/admin')
@login_required
def admin_dashboard():
    """Render the admin dashboard with statistics and user data."""
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    stats = {
        "active_users_count": User.query.count(),
        "public_campaigns_count": Campaign.query.filter_by(visibility='public').count(),
        "private_campaigns_count": Campaign.query.filter_by(visibility='private').count(),
        "ad_requests_pending": AdRequest.query.filter_by(request_status='Pending').count(),
        "ad_requests_approved": AdRequest.query.filter_by(request_status='Approved').count(),
        "ad_requests_rejected": AdRequest.query.filter_by(request_status='Rejected').count()
    }

    users = User.query.all()
    sponsors = Sponsor.query.all()
    campaigns = Campaign.query.all()

    sponsor_bio = {}
    for sponsor in sponsors:
        active_campaigns = Campaign.query.filter_by(sponsor_id=sponsor.sponsor_id).all()
        joined_influencers = User.query.join(CampaignInfluencer).filter(CampaignInfluencer.campaign_id.in_([camp.campaign_id for camp in active_campaigns])).all()
        bio = f"Active Campaigns: {', '.join(campaign.title for campaign in active_campaigns)}"
        bio += f" | Joined Influencers: {', '.join(influencer.username for influencer in joined_influencers)}"
        sponsor_bio[sponsor.sponsor_id] = bio

    return render_template('admin_dashboard.html', **stats, users=users, sponsors=sponsors, campaigns=campaigns, sponsor_bio=sponsor_bio)
@app.route('/sponsor', methods=['GET'])
@login_required
def sponsor_dashboard():
    """Render the sponsor dashboard with search functionality."""
    search_query = request.args.get('search', '')
    sponsor = Sponsor.query.filter_by(user_id=current_user.user_id).first()

    influencers = User.query.join(Influencer).filter(
        User.username.ilike(f'%{search_query}%')
    ).all()

    influencer_campaigns = {}
    for influencer in influencers:
        joined_campaigns = Campaign.query.join(CampaignInfluencer).filter(CampaignInfluencer.influencer_id == influencer.user_id).all()
        influencer_campaigns[influencer.user_id] = joined_campaigns

    return render_template('sponsor_dashboard.html', influencers=influencers, search_query=search_query, influencer_campaigns=influencer_campaigns)

@app.route('/sponsor/update_profile', methods=['GET', 'POST'])
@login_required
def update_sponsor_profile():
    """Allow sponsors to update their profile information."""
    if current_user.role != 'sponsor':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))

    sponsor = Sponsor.query.filter_by(user_id=current_user.user_id).first_or_404()
    form = UpdateSponsorForm(obj=sponsor)

    if form.validate_on_submit():
        sponsor.company = form.company.data
        sponsor.sector = form.sector.data
        sponsor.company_description = form.company_description.data
        db.session.commit()
        flash('Profile updated!', 'success')
        return redirect(url_for('sponsor_dashboard'))

    return render_template('update_sponsor_profile.html', form=form)



@app.route('/influencer')
@login_required
def influencer_dashboard():
    """Render the influencer dashboard."""
    return render_template('influencer_dashboard.html')

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Allow influencers to update their profile description."""
    new_desc = request.form.get('description')
    if new_desc:
        current_user.bio = new_desc
        db.session.commit()
        flash('Profile updated!', 'success')
    return redirect(url_for('influencer_dashboard'))


@app.route('/campaign/new', methods=['GET', 'POST'])
@login_required
def new_campaign():
    """Allow sponsors to create a new campaign."""
    form = CampaignForm()
    if form.validate_on_submit():
        campaign = Campaign(
            sponsor_id=current_user.user_id,
            title=form.title.data,
            campaign_description=form.campaign_description.data,
            start=form.start.data,
            end=form.end.data,
            campaign_budget=form.campaign_budget.data,
            visibility=form.visibility.data,
            campaign_goals=form.campaign_goals.data
        )
        db.session.add(campaign)
        db.session.commit()
        return redirect(url_for('sponsor_dashboard'))
    return render_template('create_campaign.html', form=form)


@app.route('/campaign/manage')
@login_required
def manage_campaigns():
    """Render the page for managing campaigns."""
    if current_user.role == 'sponsor':
        campaigns = Campaign.query.filter_by(sponsor_id=current_user.user_id).all()
        joined_influencers = {camp.campaign_id: User.query.join(CampaignInfluencer).filter(CampaignInfluencer.campaign_id == camp.campaign_id).all() for camp in campaigns}
        return render_template('manage_campaign.html', campaigns=campaigns, joined_influencers=joined_influencers)
    flash('Access denied.', 'danger')
    return redirect(url_for('index'))

@app.route('/campaign/edit/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
def edit_campaign(campaign_id):
    """Allow sponsors to edit their campaigns."""
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.sponsor_id != current_user.user_id:
        flash('Permission denied.', 'danger')
        return redirect(url_for('manage_campaigns'))


    form = CampaignForm(obj=campaign)
    if form.validate_on_submit():
        form.populate_obj(campaign)
        db.session.commit()
        flash('Campaign updated!', 'success')
        return redirect(url_for('manage_campaigns'))
    
    return render_template('update_campaign.html', form=form, campaign=campaign)



@app.route('/campaign/delete/<int:campaign_id>', methods=['POST'])
@login_required
def delete_campaign(campaign_id):
    """Allow sponsors to delete their campaigns."""
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.sponsor_id != current_user.user_id:
        flash('Permission denied.', 'danger')
        return redirect(url_for('manage_campaigns'))
    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign deleted!', 'success')
    return redirect(url_for('manage_campaigns'))


@app.route('/campaign/join/<int:campaign_id>', methods=['POST'])
@login_required
def join_campaign(campaign_id):
    """Allow influencers to join a campaign."""
    if current_user.role != 'influencer':
        flash('Only influencers can join campaigns.', 'danger')
        return redirect(url_for('view_campaigns'))
    if CampaignInfluencer.query.filter_by(campaign_id=campaign_id, influencer_id=current_user.user_id).first():
        flash('Already joined.', 'warning')
        return redirect(url_for('view_campaigns'))
    db.session.add(CampaignInfluencer(campaign_id=campaign_id, influencer_id=current_user.user_id))
    db.session.commit()
    flash('Joined campaign!', 'success')
    return redirect(url_for('view_campaigns'))



@app.route('/campaigns')
@login_required
def view_campaigns():
    """Render a list of public campaigns."""
    try:
        campaigns = Campaign.query.filter_by(visibility='public').all()
        user = current_user
        joined_campaigns = {camp.campaign_id: bool(CampaignInfluencer.query.filter_by(campaign_id=camp.campaign_id, influencer_id=user.user_id).first()) for camp in campaigns}
        form = AdRequestForm()
        return render_template('view_campaigns.html', campaigns=campaigns, current_user=user, joined_campaigns=joined_campaigns, form=form)
    except Exception as e:
        print(f"Error fetching campaigns: {e}")
        flash('Error fetching campaigns.', 'error')
        return redirect(url_for('index'))



@app.route('/submit_ad_request/<int:campaign_id>', methods=['POST'])
@login_required
def submit_ad_request(campaign_id):
    """Allow influencers to submit an ad request for a campaign."""
    if current_user.role != 'influencer':
        flash('Only influencers can submit ad requests.', 'danger')
        return redirect(url_for('view_campaigns'))

    form = AdRequestForm()
    if form.validate_on_submit():
        ad_request = AdRequest(
            request_content=form.request_content.data,
            payment_amount=form.payment.data,
            campaign_id=campaign_id,
            influencer_id=current_user.user_id
        )
        db.session.add(ad_request)
        db.session.commit()
        flash('Ad request submitted!', 'success')
        return redirect(url_for('view_campaigns'))

    else:
        flash('Error submitting ad request.', 'danger')
        return redirect(url_for('view_campaigns'))


@app.route('/ad_requests')
@login_required
def view_ad_requests():
    """Render a list of ad requests based on user role."""
    if current_user.role == 'sponsor':
        ad_requests = AdRequest.query.join(Campaign).filter(Campaign.sponsor_id == current_user.user_id).all()
    elif current_user.role == 'influencer':
        ad_requests = AdRequest.query.filter_by(influencer_id=current_user.user_id).all()
    else:
        ad_requests = AdRequest.query.all()
    return render_template('view_ad_requests.html', ad_requests=ad_requests)


@app.route('/ad_request/approve/<int:ad_request_id>', methods=['POST'])
@login_required
def approve_ad_request(ad_request_id):
    """Allow sponsors to approve an ad request."""
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    if current_user.role != 'sponsor' or current_user.user_id != ad_request.campaign.sponsor_id:
        flash('Permission denied.', 'danger')
        return redirect(url_for('view_ad_requests'))
    ad_request.request_status = 'Approved'
    db.session.commit()
    flash('Ad request approved!', 'success')
    return redirect(url_for('view_ad_requests'))

@app.route('/ad_request/reject/<int:ad_request_id>', methods=['POST'])
@login_required
def reject_ad_request(ad_request_id):
    """Allow sponsors to reject an ad request."""
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    ad_request.request_status = 'Rejected'
    db.session.commit()
    flash('Ad request rejected!', 'success')
    return redirect(url_for('view_ad_requests'))


@app.route('/ad_request/negotiate/<int:ad_request_id>', methods=['GET', 'POST'])
@login_required
def negotiate_ad_request(ad_request_id):
    """Allow negotiation on ad requests by either the sponsor or the influencer."""
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    if ad_request.influencer_id != current_user.user_id and current_user.role != 'sponsor':
        flash('Permission denied.', 'danger')
        return redirect(url_for('view_ad_requests'))

    if request.method == 'POST':
        new_amount = request.form.get('payment_amount')
        if new_amount:
            ad_request.payment_amount = float(new_amount)
        ad_request.request_status = 'Negotiated'
        db.session.commit()
        flash('Ad request updated!', 'success')
        return redirect(url_for('view_ad_requests'))

    form = AdRequestForm(obj=ad_request)
    return render_template('negotiate_ad_request.html', form=form, ad_request=ad_request)


@app.route('/logout')
@login_required
def logout():
    """Log out the user and redirect to homepage."""
    logout_user()
    flash('Logged out!', 'info')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)