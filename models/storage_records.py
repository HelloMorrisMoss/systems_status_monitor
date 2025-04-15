"""Contains CheckServer SQLAlchemy definition. This defines """
import sqlalchemy
from sqlalchemy import Column, ForeignKey, func, Integer, String
from sqlalchemy.orm import relationship

from helpers.dev_common import exception_one_line
from helpers.helpers import jsonize_sqla_model
from log_setup import lg
from models.model_wrapper import ModelWrapper
from models.sqla_instance import Base


class StorageRecord(Base):
    """A record of the storage available on a drive at a time using sqlalchemy declarative base to interact with the database."""

    __tablename__ = 'system_storage_records'

    db_current_ts = func.current_timestamp()

    # relationship to the system table
    id = Column(Integer, primary_key=True)
    system = relationship('SystemModel', back_populates='storage_records')
    parent_id = Column(Integer, ForeignKey('system_info.id'), nullable=False)

    # record data
    drive_letter = Column(String)
    record_timestamp = Column(sqlalchemy.DateTime(timezone=True), server_default=db_current_ts)
    bytes_free = Column(sqlalchemy.BigInteger)

    def __init__(self, **kwargs):
        # for the kwargs provided, assign them to the corresponding columns
        self_keys = StorageRecord.__dict__.keys()
        for kw, val in kwargs.items():
            if kw in self_keys:
                setattr(self, kw, val)
            else:
                lg.warning('Key %s provided does not exist as a StorageRecord table column.')

    @classmethod
    def find_by_id(cls, id_, get_sqalchemy=False):
        """Get a entry of a record by its id.

        :param id_: int, the id.
        :param get_sqalchemy: bool
        :return: class instance for entry
        """

        id_df = cls.query.filter_by(id=id_).first()
        id_df = ModelWrapper(id_df)
        return id_df

    @classmethod
    def new_record(cls, **kwargs):
        """Create a new record entry using any column values provided as keyword parameters.

        :param kwargs: dict, of kwargs['column_name'] = 'value to use'
        :return: class instance for new entry
        """

        new_def = StorageRecord(**kwargs)
        new_def.save_to_database()  # required for the database timestamp, id etc.
        return new_def

    @classmethod
    def find_all(cls):
        """Get a list of all entry records as class instances.

        :return: list
        """
        return cls.query.all()

    def save_to_database(self):
        """Save the changed to entry to the database."""

        self.session.add(self)
        try:
            self.session.commit()
        except sqlalchemy.exc.IntegrityError as sql_ierr:
            lg.warning('CheckServer "%s,%s,%s" may already exist.', self.parent_id, self.port, self.address_suffix)
            self.session.rollback()
        except Exception as exc:
            lg.error(exception_one_line(exception_obj=exc))
            self.session.rollback()

    def get_model_dict(self):
        """Get a dictionary of {column_name: value} for the entry.

        :return: dict
        """
        jdict = {}
        for key in self.__table__.columns.keys():
            jdict[key] = self.__dict__.get(key)
        return jdict

    def jsonizable(self):
        """Get a json string representing the entry.

        :return: str
        """

        return jsonize_sqla_model(self)

    def __repr__(self):
        """Much like the base object.__repr__ but adding in the record columns for visibility.

        ex:
        with SystemModel.session() as sesn:
            for stm in SystemModel.find_all():
            print(stm.storage_records)
        [<models.storage_records.StorageRecord at 0x220783ae690: {'id': 1, 'parent_id': 0, 'drive_letter': 'd',
        'record_timestamp': '2025-04-15T14:36:39.988201-04:00', 'bytes_free': 4413288448}>]
        """
        my_type = type(self)
        module = my_type.__module__
        class_name = my_type.__name__
        return f'<{module}.{class_name} at {hex(id(self))}: {self.jsonizable()}>'
