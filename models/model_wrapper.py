"""A wrapper class that will hold the column values and recreate a model instance when needed."""


class ModelWrapper:
    def __init__(self, model_instance):
        self._model_instance = model_instance

        for key in self._model_instance.__table__.columns.keys():
            this_val = getattr(self._model_instance, key)
            setattr(self, key, this_val)

    def reconnect_model(self):
        self._model_instance


if __name__ == '__main__':
    import sqlalchemy as sqla
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker, declarative_base

    DATABASE_URI = 'sqlite:///:memory:'
    engine = create_engine(DATABASE_URI, pool_pre_ping=True)

    Base = declarative_base()


    class DummyModel(Base):
        __tablename__ = '__dummy_table__'

        id_ = sqla.Column(primary_key=True, type_=sqla.Integer)
        data = sqla.Column(sqla.TEXT)


    Base.metadata.create_all(engine)

    # original session: create a record, save it to the database, use the ModelWrapper
    sesmkr = sessionmaker(bind=engine)
    with sesmkr() as session0:
        dm0 = DummyModel()
        session0.add(dm0)
        session0.commit()
        wrp0 = ModelWrapper(dm0)

    pass  # at this point, because of the wrp0(why?), dm0 is detached but accessible
    print(f'dm0 detached state: {dm0._sa_instance_state.detached}')

    # reattach to new session
    with sesmkr() as session1:
        dm0.data = 'words'
        session1.add(dm0)
        session1.commit()
        # wrp1 = ModelWrapper(dm0)  # without this, will get detached instance error accessing columns
        dumdum = dm0  # this is not sufficient
    '''sqlalchemy.orm.exc.DetachedInstanceError: Instance <DummyModel at 0x1a7f6e5a550> is not bound to a Session;
    attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/14/bhk3)'''
    pass  # at this point, since wrp1 is commented out, dm0 is detached but not accessible
