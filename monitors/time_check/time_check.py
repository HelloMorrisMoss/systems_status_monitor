import datetime


def seconds_between(start: datetime.datetime, end: datetime.datetime) -> float:
    """
    Calculate the number of seconds between two datetime.datetime objects.

    :param start: A datetime.datetime object representing the start time.
    :param end: A datetime.datetime object representing the end time.
    :return: A float representing the number of seconds between the start and end times.
    """

    # Calculate the difference between the start and end times as a timedelta object
    time_difference: datetime.timedelta = end - start

    # Convert the time difference to seconds as a float and return the result
    return time_difference.total_seconds()
