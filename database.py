from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL="sqlite:///./mems.db" ## address of the database file

engine=create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
) ## create engine to connect to the database

SessionLocal=sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
) ## create a sessionmaker class to create database sessions

Base=declarative_base() ## create a base class for the models to inherit from 

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
## a dependency function to get a database session and close it after use