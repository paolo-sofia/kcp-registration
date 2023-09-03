import datetime


def is_expired(data_registrazione: datetime.datetime) -> bool:
    return (datetime.date.today() - data_registrazione.date()).days <= 365