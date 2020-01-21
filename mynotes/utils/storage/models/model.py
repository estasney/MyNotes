from sqlalchemy import Column, Integer, Text, Table, ForeignKey
from sqlalchemy.orm import relationship, backref
from .meta import Base

module_notebook = Table('module_notebook', Base.metadata,
                        Column('module_id', Integer, ForeignKey('modules.id')),
                        Column('notebook_id', Integer, ForeignKey('notebooks.id'))
                        )

module_category = Table('module_category', Base.metadata,
                        Column('module_id', Integer, ForeignKey('modules.id')),
                        Column('notebook_id', Integer, ForeignKey('categories.id'))
                        )


class Module(Base):
    __tablename__ = 'modules'
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    notebooks = relationship("Notebook",
                             secondary=module_notebook,
                             back_populates='modules')
    categories = relationship("Category",
                              secondary=module_category,
                              back_populates='modules')


class Notebook(Base):
    __tablename__ = "notebooks"
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    modules = relationship("Module",
                           secondary=module_notebook,
                           back_populates='notebooks')
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship("Category", back_populates='notebooks')


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    children_categories = relationship("Category",
                                       backref=backref('parent', remote_side=[id]))
    notebooks = relationship("Notebook", back_populates='category')
    categories = relationship("Module", back_populates='categories')
