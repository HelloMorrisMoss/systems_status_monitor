"""Contains CheckServer SQLAlchemy definition. This defines """
import sqlalchemy
from sqlalchemy import Column, ForeignKey, func, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from helpers.dev_common import exception_one_line
from helpers.helpers import jsonize_sqla_model
from log_setup import lg
from models.model_wrapper import ModelWrapper
from models.sqla_instance import Base


class CheckServer(Base):
    """A model of the computer systems using sqlalchemy declarative base to interact with the database."""

    __tablename__ = 'check_server'
    __table_args__ = (
        UniqueConstraint('parent_id', 'port', 'address_suffix', name='unique_check_server'),
    )

    db_current_ts = func.current_timestamp()

    id = Column(Integer, primary_key=True)
    system = relationship('SystemModel', back_populates='check_servers')
    parent_id = Column(Integer, ForeignKey('system_info.id'), nullable=False)

    port = Column(String)
    address_suffix = Column(String)
    status_condition_type = Column(String)
    status_condition_value_data = Column(JSONB)

    def __init__(self, **kwargs):
        # for the kwargs provided, assign them to the corresponding columns
        self_keys = CheckServer.__dict__.keys()
        for kw, val in kwargs.items():
            if kw in self_keys:
                setattr(self, kw, val)
            else:
                lg.warning('Key %s provided does not exist as a CheckServer table column.')

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
    def new_system(cls, system_id, **kwargs):
        """Create a new system entry using any column values provided as keyword parameters.

        :param kwargs: dict, of kwargs['column_name'] = 'value to use'
        :return: class instance for new entry
        """
        # TODO: rework test for existing system entry
        # existing_systems = [stm for stm in cls.query.filter_by(hostname=kwargs['hostname'])]
        # if len(existing_systems):
        #     lg.warning('System "%s" may already exist.', kwargs['hostname'])
        # else:
        new_def = CheckServer(**kwargs)
        new_def.save_to_database()
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
