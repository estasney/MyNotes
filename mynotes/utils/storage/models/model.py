from sqlalchemy import Column, Integer, Text, Table, ForeignKey
from sqlalchemy.orm import relationship, backref
from .meta import Base

module_notebook = Table('module_notebook', Base.metadata,
                        Column('module_id', Integer, ForeignKey('modules.id')),
                        Column('notebook_id', Integer, ForeignKey('notebooks.id'))
                        )

keyword_notebook = Table('keyword_notebook', Base.metadata,
                         Column('keyword_id', Integer, ForeignKey('keywords.id')),
                         Column('notebook_id', Integer, ForeignKey('notebooks.id'))
                         )

module_category = Table('module_category', Base.metadata,
                        Column('module_id', Integer, ForeignKey('modules.id')),
                        Column('category_id', Integer, ForeignKey('categories.id'))
                        )

keyword_category = Table('keyword_category', Base.metadata,
                         Column('keyword_id', Integer, ForeignKey('keywords.id')),
                         Column('category_id', Integer, ForeignKey('categories.id'))
                         )


class Keyword(Base):
    __tablename__ = "keywords"

    JSON_KEYS = ['id', 'name']

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    notebooks = relationship("Notebook",
                             secondary=keyword_notebook,
                             back_populates='keywords')
    categories = relationship("Category",
                              secondary=module_category,
                              back_populates='modules')

    def to_dict(self) -> dict:
        d = {k: getattr(self, k, None) for k in self.JSON_KEYS}
        d['table'] = self.__tablename__
        return d


class Module(Base):
    __tablename__ = 'modules'

    JSON_KEYS = ['id', 'name']

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    notebooks = relationship("Notebook",
                             secondary=module_notebook,
                             back_populates='modules')
    categories = relationship("Category",
                              secondary=module_category,
                              back_populates='modules')

    def to_dict(self) -> dict:
        d = {k: getattr(self, k, None) for k in self.JSON_KEYS}
        d['table'] = self.__tablename__
        return d


class Notebook(Base):
    __tablename__ = "notebooks"

    JSON_KEYS = ['id', 'name', 'display_name', 'title', 'category_id', 'description']

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    display_name = Column(Text)
    description = Column(Text, default='')
    title = Column(Text)
    modules = relationship("Module",
                           secondary=module_notebook,
                           back_populates='notebooks')
    keywords = relationship("Keyword",
                            secondary=keyword_notebook,
                            back_populates='notebooks')
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship("Category", back_populates='notebooks')

    def to_dict(self, url_base) -> dict:
        d = {k: getattr(self, k, None) for k in self.JSON_KEYS}
        d['table'] = self.__tablename__
        if url_base:
            url = url_base + "/" + self.name
        else:
            url = "/" + self.name
        d['url'] = url
        d['modules'] = [m.to_dict() for m in self.modules]
        d['keywords'] = [kw.to_dict() for kw in self.keywords]
        return d


class Category(Base):
    __tablename__ = "categories"

    JSON_KEYS = ['id', 'name', 'display_name', 'parent_id', 'url']

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    display_name = Column(Text)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    children_categories = relationship("Category",
                                       backref=backref('parent', remote_side=[id]))
    notebooks = relationship("Notebook", back_populates='category')
    modules = relationship("Module",
                           secondary=module_category,
                           back_populates='categories')
    keywords = relationship("Keyword",
                            secondary=keyword_category,
                            back_populates="categories")

    @property
    def url(self):
        parent = self.parent
        if not parent:
            return self.name
        return parent.url + "/" + self.name

    def to_dict(self):
        d = {k: getattr(self, k, None) for k in self.JSON_KEYS}
        d['table'] = self.__tablename__
        # noinspection PyTypeChecker
        d['has_children'] = len(self.children_categories) > 0
        d['children'] = [c.to_dict() for c in self.children_categories]
        d['notebooks'] = [n.to_dict(self.url) for n in self.notebooks]
        d['modules'] = [m.to_dict() for m in self.modules]
        d['keywords'] = [kw.to_dict() for kw in self.keywords]
        return d
