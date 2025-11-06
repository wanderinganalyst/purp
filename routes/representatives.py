from flask import Blueprint, render_template, session, flash, redirect, url_for
from services.representatives import get_all_reps, get_rep_by_name
from services.web_utils import fetch_remote_page

reps_bp = Blueprint('reps', __name__)

@reps_bp.route('/representatives')
def reps_list():
    """Display list of all representatives."""
    reps = get_all_reps()
    return render_template('reps.html', members=reps)

@reps_bp.route('/representative/<name>')
def rep_detail(name):
    """Display details of a specific representative."""
    rep = get_rep_by_name(name)
    if not rep:
        flash('Representative not found.')
        return redirect(url_for('reps.reps_list'))
    return render_template('rep_detail.html', rep=rep)