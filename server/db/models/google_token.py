# START OF FILE db/models/google_token.py

from tortoise import fields
from tortoise.models import Model


class GoogleToken(Model):
    """
    Stores Google API authorization tokens for a user.
    """
    id = fields.IntField(pk=True)
    # One-to-one relationship with the User model.
    # If a user is deleted, their token is also deleted (on_delete=fields.CASCADE).
    user = fields.OneToOneField("models.User", related_name="google_token", on_delete=fields.CASCADE)
    
    # The fields below match the structure of credentials from google-auth-oauthlib
    token = fields.TextField()
    refresh_token = fields.TextField(null=True)
    token_uri = fields.TextField()
    client_id = fields.TextField()
    client_secret = fields.TextField()
    scopes = fields.JSONField()

    class Meta:
        table = "google_tokens"