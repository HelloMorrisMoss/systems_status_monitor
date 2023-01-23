import datetime

# import requests
from sqlalchemy.types import TIMESTAMP, TypeDecorator


def format_storage_bytes(size: int, decimals: int = 2, binary_system: bool = True) -> str:
    """Convert bytes size to human-readable units.

    Originally from
    https://lindevs.com/code-snippets/convert-file-size-in-bytes-into-human-readable-string-using-python

    :param size: int, the number of bytes.
    :param decimals: int, the number of decimal places to display.
    :param binary_system: bool, use 1024 instead of 1000 bytes as the step size.
    :return: str, the formatted size of the
    """

    if binary_system:
        units = 'B', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB'
        largest_unit = 'YiB'
        step: int = 1024
    else:
        units = 'B', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB'
        largest_unit = 'YB'
        step: int = 1000

    unit: str
    for unit in units:
        if size < step:
            return f'{size:.{decimals}f} {unit}'
        size /= step
    return f'{size:.{decimals}f} {largest_unit}'


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
