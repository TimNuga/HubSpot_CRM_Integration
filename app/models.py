from datetime import datetime
from app.extensions import db

class CreatedCRMObject(db.Model):
    """
    Tracks newly created or updated objects in HubSpot.
    Helps us implement custom queries, track timestamps, etc.
    Example usage: Insert a record every time we create or update a contact/deal/ticket.
    """
    __tablename__ = "created_crm_objects"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    object_id = db.Column(db.String(255), nullable=False, index=True)
    object_type = db.Column(db.String(50), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CreatedCRMObject {self.object_type} - {self.object_id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "object_id": self.object_id,
            "object_type": self.object_type,
            "created_at": self.created_at.isoformat()
        }
