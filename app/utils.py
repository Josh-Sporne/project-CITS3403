import os
import uuid

from flask import current_app, request
from werkzeug.utils import secure_filename


# Image extensions we're willing to accept. Mirrors the FileAllowed validators
# on RecipeForm.image and EditProfileForm.image so the server-side check stays
# in lockstep with form-level validation (defence in depth).
ALLOWED_IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}


def json_body():
    data = request.get_json(silent=True)
    if data is None:
        current_app.logger.debug('json_body: missing or malformed JSON body')
        return {}
    if not isinstance(data, dict):
        current_app.logger.debug('json_body: JSON body was not an object')
        return {}
    return data


def save_uploaded_image(file_storage):
    """Save an uploaded image to UPLOAD_FOLDER with a random filename.

    Returns the saved filename (relative to UPLOAD_FOLDER), or None if the
    upload is missing or has an unrecognised extension.

    Defends against three failure modes the inline rsplit('.', 1)[-1] pattern
    had:
      1. Filename with no dot — rsplit would return the whole filename as the
         "extension", producing files like `uuidfilenamejpg` with no real ext.
      2. Filename with a non-image extension — would still be saved with that
         extension. Form-level FileAllowed catches normal flows, but a hand-
         crafted request bypassing the form wouldn't be checked.
      3. secure_filename() not called — UUID-renaming masked any path traversal,
         but defence in depth is cheap.
    """
    if not file_storage or not getattr(file_storage, 'filename', None):
        return None

    safe_name = secure_filename(file_storage.filename)
    if '.' not in safe_name:
        return None
    ext = safe_name.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTS:
        return None

    filename = f'{uuid.uuid4().hex}.{ext}'
    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)
    file_storage.save(os.path.join(upload_dir, filename))
    return filename
