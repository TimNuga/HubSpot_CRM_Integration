import datetime
from app.extensions import db


class HubspotAuth(db.Model):
    """
    Stores OAuth tokens for HubSpot.
    """

    __tablename__ = "hubspot_auth"

    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String(1024), nullable=False)
    refresh_token = db.Column(db.String(1024), nullable=False)
    token_expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )

    def __repr__(self):
        return f"<HubspotAuth id={self.id} token_expires_at={self.token_expires_at}>"


class CreatedCRMObject(db.Model):
    """
    Stores newly created or updated CRM objects (contacts, deals, tickets) in local DB.
    This table helps track new objects so that they can be retrieved
    via local endpoints (e.g. GET /api/new-crm-objects).
    """

    __tablename__ = "created_crm_objects"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(128), nullable=False)  # e.g., HubSpot object ID
    object_type = db.Column(
        db.String(32), nullable=False
    )  # "contacts", "deals", "tickets"
    name = db.Column(
        db.String(255), nullable=True
    )  # e.g., email or dealname or subject
    created_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.utcnow
    )
    updated_date = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    def __repr__(self):
        return f"<CreatedCRMObject id={self.id}, type={self.object_type}, external_id={self.external_id}>"
