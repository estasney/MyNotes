import models.meta
import models.model

def main():
    engine = models.meta.get_engine()
    models.model.Base.metadata.create_all(engine)


if __name__ == '__main__':
    main()
