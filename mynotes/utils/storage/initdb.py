import models.meta
from models import *


def main():
    engine = models.meta.get_engine()
    models.meta.Base.metadata.create_all(engine)


if __name__ == '__main__':
    main()
