from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Track(Base):
	__tablename__ = "tracks"
	id = Column(Integer, primary_key=True)
	path = Column(String, unique=True)
	duration = Column(Float)
	sha1 = Column(String, unique=True)
	fingerprint = Column(String)
	embedding = Column(String, nullable=True)
	cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)

class Cluster(Base):
	__tablename__ = "clusters"
	id = Column(Integer, primary_key=True)
	name = Column(String)
	tracks = relationship("Track", backref="cluster")
