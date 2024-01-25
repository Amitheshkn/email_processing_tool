import configparser
from typing import Any, Type

from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

config = configparser.ConfigParser()
config.read('config.ini')

data_base_config = config["DATABASE"]
DATABASE_HOST = data_base_config["DATABASE_HOST"]
DATABASE_PASSWORD = data_base_config["DATABASE_PASSWORD"]
DATABASE_PORT = data_base_config["DATABASE_PORT"]
DATABASE_USER_NAME = data_base_config["DATABASE_USER_NAME"]
DATABASE_NAME = data_base_config["DATABASE_NAME"]

DATABASE_URI = (f"postgresql://{DATABASE_USER_NAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:"
                f"{DATABASE_PORT}/{DATABASE_NAME}")

Base = declarative_base()

engine = create_engine(DATABASE_URI)


class Email(Base):
    __tablename__ = 'emails'
    id = Column(String, primary_key=True, nullable=False)
    subject = Column(String)
    from_address = Column(String, nullable=False)
    date_received = Column(DateTime(timezone=True), nullable=False)
    message_body = Column(Text)


class DatabaseService:
    def __init__(self) -> None:
        self.engine = create_engine(DATABASE_URI)
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def add_emails(self, emails: list[dict[str, Any]]) -> None:
        db = self.session()
        try:
            for email_data in emails:
                email = Email(**email_data)
                db.add(email)
            db.commit()
            print("Emails fetched have been successfully stored")
        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def fetch_emails(self) -> list[Type[Email]]:
        db = self.session()
        try:
            return db.query(Email).all()

        except Exception as e:
            print(f"Error occurred: {str(e)}")
            return []

        finally:
            db.close()
