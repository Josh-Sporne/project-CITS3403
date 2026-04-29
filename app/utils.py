from flask import request

def json_body():
    data = request.get_json(silent=True)
    if data is None:
        from flask import current_app
        current_app.logger.debug('json_body: missing or malformed JSON body')
        return {}
    return data
