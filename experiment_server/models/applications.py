""" This is a schema """
from sqlalchemy import (
    Column,
    Integer,
    Text
)

from sqlalchemy.orm import relationship
from .meta import Base


class Application(Base):
    """ This is definition of class Application """
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    configurationkeys = relationship("ConfigurationKey", backref="application")

    def as_dict(self):
        """ transfer data to dictionary """
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}
