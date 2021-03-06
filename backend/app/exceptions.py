# -*- coding: future_fstrings -*-
from flask import jsonify


def template(message='An error has occurred', code=500):
    return {'message': message, 'status_code': code}


USER_NOT_FOUND = template('User not found', code=404)
USER_ALREADY_REGISTERED = template('User already registered', code=422)
SESSION_NOT_FOUND = template('Invalid session', code=422)
UNKNOWN_ERROR = template(code=500)


class InvalidUsage(Exception):
  def __init__(self, message, status_code=None, payload=None):
    Exception.__init__(self)
    self.message = message
    if status_code is not None:
      self.status_code = status_code
    self.payload = payload

  def to_json(self):
    rv = dict(self.payload or ())
    rv['message'] = self.message
    return jsonify(rv)

  @classmethod
  def user_not_found(cls):
    return cls(**USER_NOT_FOUND)

  @classmethod
  def user_already_registered(cls):
    return cls(**USER_ALREADY_REGISTERED)

  @classmethod
  def session_not_found(cls):
    return cls(**SESSION_NOT_FOUND)

  @classmethod
  def unknown_error(cls):
    return cls(**UNKNOWN_ERROR)
