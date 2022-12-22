import datetime

# import requests
from sqlalchemy.types import TIMESTAMP, TypeDecorator


class Timestamp(TypeDecorator):
    impl = TIMESTAMP

    def process_bind_param(self, value, dialect):
        if value is None:
            return None

        if isinstance(value, datetime.datetime):
            return value.isoformat()

        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        return datetime.datetime.fromisoformat(value)


def jsonize_sqla_model(model):
    """Get a json serializable representation of the SQLAlchemy Model instance.

    This is needed due to datetimes, they are converted to ISO 8601 format strings.

    :return: dict
    """

    jdict = {}
    for key in model.__table__.columns.keys():
        this_val = getattr(model, key)
        if isinstance(this_val, datetime.datetime):
            try:
                this_val = this_val.isoformat()
            except AttributeError as er:
                this_val = str(this_val)

        jdict[key] = this_val
    return jdict


def remove_empty_parameters(data):
    """Accepts a dictionary and returns a dict with only the key, values where the values are not None."""

    return {key: value for key, value in data.items() if value is not None}

# def check_for_existing_instance() -> Union[requests.Response, None]:
#     """Attempts to connect to an existing web server to get the status of the popup.
#
#     :return: requests.Response, or None if a connection could not be made.
#     """
#     import requests
#     from log_setup import lg
#
#     try:
#         response: requests.Response = requests.get('http://0.0.0.0:5000/popup_status')
#         lg.debug(response)
#     except requests.exceptions.ConnectionError:
#         response: None = None
#
#     return response
