import collections
import datetime
from hashlib import md5
from abc import abstractmethod, ABCMeta
from six import add_metaclass
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_login import UserMixin
from flask_sqlalchemy import BaseQuery
from operator import attrgetter

from app import db

class TimeQuery(BaseQuery):
  def _within_interval(self, user_id, is_valid):
    now, result = datetime.datetime.now(), []
    for item in self.filter_by(user_id=user_id).all():
      delta = now - item.creation_time
      if is_valid(delta):
        result.append(item)
    return result

  def today(self, user_id):
    return self._within_interval(user_id,
        is_valid = lambda d: d.days <= 1)

  def last_month(self, user_id):
    return self._within_interval(user_id,
        is_valid = lambda d: d.days <= 30)

  def last_week(self, user_id):
    return self._within_interval(user_id,
      is_valid = lambda d: d.days <= 7)


class TimeModel(db.Model):
  __abstract__ = True
  query_class = TimeQuery

  @property
  @abstractmethod
  def creation_time(self):
    """Returns the creation date."""


@add_metaclass(ABCMeta)
class Statistics(object):
  @staticmethod
  @abstractmethod
  def _generate_stat(user_id, field_getter):
    """Return max statistics for a specified category
     within a specified period of time."""

  @classmethod
  def get_words(cls, user_id):
    return cls._generate_stat(user_id,
        field_getter = lambda s: s.words)

  @classmethod
  def get_accuracy(cls, user_id):
    return cls._generate_stat(user_id,
        field_getter = lambda s: s.accuracy)

  @classmethod
  def get_chars(cls, user_id):
    return cls._generate_stat(user_id,
        field_getter = lambda s: s.chars)


class DailyStats(Statistics):
  @staticmethod
  def _generate_stat(user_id, field_getter):
    sessions, result = Session.query.today(user_id), {}
    for session in sessions:
      time = session.created_date
      time = '{}:{}'.format(time.hour, time.minute)
      result[time] = max(result.get(time, -1), field_getter(session))
    strptime =datetime.datetime.strptime
    result = sorted(result.items(),
      key = lambda x: strptime(x[0],'%H:%M').time())
    return collections.OrderedDict(result)


class WeeklyStats(Statistics):
  @staticmethod
  def _generate_stat(user_id, field_getter):
    sessions, result = Session.query.last_week(user_id), {}
    for session in sessions:
      day = session.created_date.day
      result[day] = max(result.get(day, -1), field_getter(session))
    return result


class MonthlyStats(Statistics):
  @staticmethod
  def _generate_stat(user_id, field_getter):
    sessions, result = Session.query.last_month(user_id), {}
    for session in sessions:
      day = session.created_date.day
      result[day] = max(result.get(day, -1), field_getter(session))
    return result


class Session(TimeModel):
  __tablename__ = 'sessions'

  id = db.Column(db.Integer, primary_key=True)
  words = db.Column(db.Integer)
  chars = db.Column(db.Integer)
  accuracy = db.Column(db.Float)
  created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

  @property
  def creation_time(self):
    return self.created_date

  def __repr__(self):
    return '<Session {!r}>'.format(self.words)


class User(db.Model, UserMixin):
  __tablename__ = 'users'

  id = db.Column(db.Integer, primary_key=True)
  social_id = db.Column(db.String(128), unique=True)
  email = db.Column(db.String(64), unique=True, index=True)
  username = db.Column(db.String(64), unique=True, index=True)
  password_hash = db.Column(db.String(128))

  @property
  def password(self):
    raise AttributeError('password is not readable')

  @password.setter
  def password(self, password):
    self.password_hash = generate_password_hash(password)

  def _get_average(self, field_getter):
    sessions = Session.query.filter_by(user_id=self.id).all()
    return sum(field_getter(s) for s in sessions) / len(sessions)

  @property
  def sessions_taken(self):
    return len(Session.query.filter_by(user_id=self.id).all())

  @property
  def words_score(self):
    return self._get_average(
      field_getter = lambda x: x.words
    )

  @property
  def accuracy_score(self):
    return round(self._get_average(
      field_getter = lambda x: x.accuracy
    ))

  @property
  def chars_score(self):
    return self._get_average(
      field_getter = lambda x: x.chars
    )

  def avatar(self, size):
    digest = md5(self.email.lower().encode('utf-8')).hexdigest()
    return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

  def verify_password(self, password):
    # if the user signed up with a provider, deny
    if not self.password_hash:
      return False
    return check_password_hash(self.password_hash, password)

  def __repr__(self):
    return '<User {!r}>'.format(self.username)
