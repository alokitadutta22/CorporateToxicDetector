import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Setup SQLite database for Enterprise Auditing
os.makedirs("data", exist_ok=True)
DB_PATH = "sqlite:///data/corporate_audit.db"
engine = create_engine(DB_PATH)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class AuditLog(Base):
    __tablename__ = "inference_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    original_text_masked = Column(String, nullable=False)
    ml_score = Column(Float)
    llm_confidence = Column(Float)
    hybrid_score = Column(Float)
    risk_level = Column(String)
    policy_violation = Column(String)

# Initialize database implicitly on startup
Base.metadata.create_all(engine)
print(f"📁 Enterprise Audit Database initialized at data/corporate_audit.db")

def log_inference(masked_text: str, result: dict):
    """Log the prediction result to the persistent local database."""
    with Session() as session:
        log = AuditLog(
            original_text_masked=masked_text,
            ml_score=result['ml_score'],
            llm_confidence=result['llm_confidence'],
            hybrid_score=result['hybrid_score'],
            risk_level=result['risk_level'],
            policy_violation=result.get('policy_violation', 'None')
        )
        session.add(log)
        session.commit()

def get_recent_logs(limit: int = 50):
    """Retrieve recent audit logs for the dashboard."""
    with Session() as session:
        logs = session.query(AuditLog).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()
        # Detach from session so they can be used outside
        session.expunge_all()
        return logs
