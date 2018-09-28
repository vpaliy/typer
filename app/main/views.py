import os
import re
import json

from flask import render_template, jsonify, request, redirect, url_for
from flask_login import login_required, current_user

from app import db
from app.models import Session, User
from app.main import main

WORD_RE = re.compile('\w+')

@main.route('/')
@main.route('/practice')
def practice():
  return render_template('main/practice.html')


@main.route('/profile/<path:username>')
def profile(username):
  user = User.query.filter_by(username=username).first()
  if user is not None:
    return render_template('main/profile.html', username=username)


# TODO: secure this
@main.route('/_words')
def words():
  # TODO: replace this
  with open(os.path.join(os.path.dirname(__file__), 'words.txt')) as f:
    words = f.read()
  words = WORD_RE.findall(words)
  return jsonify(result=words)


# TODO: secure this
@main.route('/save', methods=('POST',))
def save():
  if not current_user.is_authenticated:
    abort(400)
  session = Session()
  session.user_id = current_user.id
  session.accuracy = request.json['accuracy']
  session.words = request.json['correct']
  session.chars = request.json['chars']
  db.session.add(session)
  db.session.commit()
  return redirect(url_for('main.practice'))


@main.route('/scores')
@login_required
def scores():
  return render_template('main/scores.html')


# TODO: secure this
@main.route('/stats')
@login_required
def statistics():
  sessions = Session.query.all()
  return jsonify(result=sessions)
