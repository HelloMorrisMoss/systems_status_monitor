import sqlalchemy
import sqlalchemy_utils
from sqlalchemy import func
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

from helpers.dev_common import exception_one_line
from helpers.helpers import jsonize_sqla_model
from log_setup import lg
from models.model_wrapper import ModelWrapper
from sqla_instance import Base
from untracked_config.cryptokey import AES_key


class SystemModel(Base):
    """A model of the computer systems using sqlalchemy declarative base to interact with the database."""

    __tablename__ = 'system_info'

    db_current_ts = func.current_timestamp()

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    hostname = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    static_ip = sqlalchemy.Column(sqlalchemy.String)

    # credentials
    username = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    password = sqlalchemy.Column(sqlalchemy_utils.StringEncryptedType(sqlalchemy.Unicode, AES_key, AesEngine),
                                 nullable=False)

    # entry metadata
    entry_created_ts = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True), server_default=db_current_ts)
    entry_modified_ts = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True), server_default=db_current_ts,
                                          onupdate=db_current_ts)
    entry_retired_ts = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True))
    record_creation_source = sqlalchemy.Column(sqlalchemy.String())

    def __init__(self, **kwargs):
        # for the kwargs provided, assign them to the corresponding columns
        self_keys = SystemModel.__dict__.keys()
        for kw, val in kwargs.items():
            if kw in self_keys:
                setattr(self, kw, val)

    @classmethod
    def find_by_id(cls, id_, get_sqalchemy=False):
        """Get a DefectModel of a record by its id.

        :param id_: int, the id.
        :param get_sqalchemy: bool
        :return: DefectModel
        """

        id_df = cls.query.filter_by(id=id_).first()
        id_df = ModelWrapper(id_df)
        return id_df

    @classmethod
    def new_system(cls, **kwargs):
        """Create a new defect using any column values provided as keyword parameters.

        :param kwargs: dict, of kwargs['column_name'] = 'value to use'
        :return: DefectModel
        """
        new_def = SystemModel(**kwargs)
        new_def.save_to_database()
        return new_def

    @classmethod
    def find_all(cls):
        """Get a list of all defect record as DefectModels.

        :return: list
        """
        return cls.query.all()

    def save_to_database(self):
        """Save the changed to defect to the database."""

        self.session.add(self)
        try:
            self.session.commit()
        except Exception as exc:
            lg.error(exception_one_line(exception_obj=exc))
            self.session.rollback()

    def get_model_dict(self):
        """Get a dictionary of {column_name: value}

        :return: dict
        """
        jdict = {}
        for key in self.__table__.columns.keys():
            jdict[key] = self.__dict__.get(key)
        return jdict

    def jsonizable(self):
        return jsonize_sqla_model(self)


if __name__ == '__main__':
    # Base.metadata.create_all()

    with SystemModel.session() as sesn:
        demo_dict = dict(hostname='demo_server',
                         static_ip='localhost',
                         username='su',
                         password='password'
                         )
        SystemModel.new_system(**demo_dict)