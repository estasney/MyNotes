from typing import ClassVar

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import backref, declarative_base, relationship

Base = declarative_base()

module_notebook = Table(
    "module_notebook",
    Base.metadata,
    Column("module_id", Integer, ForeignKey("modules.name")),
    Column("notebook_id", Integer, ForeignKey("notebooks.name")),
)

keyword_notebook = Table(
    "keyword_notebook",
    Base.metadata,
    Column("keyword_id", Integer, ForeignKey("keywords.name")),
    Column("notebook_id", Integer, ForeignKey("notebooks.name")),
)

module_category = Table(
    "module_category",
    Base.metadata,
    Column("module_id", Integer, ForeignKey("modules.name")),
    Column("category_id", Integer, ForeignKey("categories.name")),
)

keyword_category = Table(
    "keyword_category",
    Base.metadata,
    Column("keyword_id", Integer, ForeignKey("keywords.name")),
    Column("category_id", Integer, ForeignKey("categories.name")),
)


class BaseModel(Base):
    __abstract__ = True

    JSON_KEYS: ClassVar[list[str]]

    def to_dict(self) -> dict:
        return {
            **{k: getattr(self, k, None) for k in self.JSON_KEYS},
            "table": self.__tablename__,
        }


class Keyword(BaseModel):
    __tablename__ = "keywords"

    JSON_KEYS = ["name"]
    name = Column(String, primary_key=True)
    notebooks = relationship(
        "Notebook", secondary=keyword_notebook, back_populates="keywords"
    )
    categories = relationship(
        "Category", secondary=keyword_category, back_populates="keywords"
    )


class Module(BaseModel):
    __tablename__ = "modules"

    JSON_KEYS = ["name"]

    name = Column(String, primary_key=True)
    notebooks = relationship(
        "Notebook", secondary=module_notebook, back_populates="modules"
    )
    categories = relationship(
        "Category", secondary=module_category, back_populates="modules"
    )


class Notebook(BaseModel):
    __tablename__ = "notebooks"

    JSON_KEYS = [
        "name",
        "display_name",
        "title",
        "category_id",
        "description",
        "created",
        "updated",
    ]

    name = Column(String, primary_key=True)
    display_name = Column(Text)
    description = Column(Text, default="")
    created = Column(DateTime)
    updated = Column(DateTime)
    title = Column(Text)
    modules = relationship(
        "Module", secondary=module_notebook, back_populates="notebooks"
    )
    keywords = relationship(
        "Keyword", secondary=keyword_notebook, back_populates="notebooks"
    )
    category_name = Column(String, ForeignKey("categories.name"))
    category = relationship("Category", back_populates="notebooks")

    def to_dict(self) -> dict:
        url = f"{self.category.url}/{self.name}"
        modules = [m.to_dict() for m in self.modules]
        keywords = [kw.to_dict() for kw in self.keywords]
        return {
            **super().to_dict(),
            "url": url,
            "modules": modules,
            "keywords": keywords,
        }


class Category(BaseModel):
    __tablename__ = "categories"

    JSON_KEYS = ["name", "display_name", "parent_id", "url"]

    name = Column(String, primary_key=True)
    display_name = Column(Text)
    parent_name = Column(Integer, ForeignKey("categories.name"), nullable=True)
    children_categories = relationship(
        "Category", backref=backref("parent", remote_side=[name])
    )
    notebooks = relationship("Notebook", back_populates="category")
    modules = relationship(
        "Module", secondary=module_category, back_populates="categories"
    )
    keywords = relationship(
        "Keyword", secondary=keyword_category, back_populates="categories"
    )

    @property
    def url(self) -> str:
        parent = self.parent
        if not parent:
            return self.name
        return parent.url + "/" + self.name

    def to_dict(self) -> dict:
        children_objs: list["Category"] = self.children_categories
        has_children = len(children_objs) > 0
        children = [c.to_dict() for c in children_objs]
        notebook_objs: list["Notebook"] = self.notebooks
        notebooks = [n.to_dict() for n in notebook_objs]
        modules = [m.to_dict() for m in self.modules]
        keywords = [kw.to_dict() for kw in self.keywords]
        return {
            **super().to_dict(),
            "has_children": has_children,
            "children": children,
            "notebooks": notebooks,
            "modules": modules,
            "keywords": keywords,
        }
