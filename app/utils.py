from flask import current_app, request


def json_body():
    data = request.get_json(silent=True)
    if data is None:
        current_app.logger.debug('json_body: missing or malformed JSON body')
        return {}
    if not isinstance(data, dict):
        current_app.logger.debug('json_body: JSON body was not an object')
        return {}
    return data
