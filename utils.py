import hmac
import json
import os
from flask import Response


# https://github.com/looker-open-source/actions/blob/master/docs/action_api.md#authentication
# authenticate all requests from Looker by evaluating authorization token
def authenticate(request):
    if request.method != 'POST' or 'authorization' not in request.headers:
        error = 'Request must be POST with auth token'
        response = {'looker': {'success': False, 'message': error}}
        print(response)
        return Response(json.dumps(response), status=401, mimetype='application/json')
    else:
        expected_auth_header = 'Token token="{}"'.format(
            os.environ.get('LOOKER_AUTH_TOKEN'))
        submitted_auth = request.headers['authorization']
        if hmac.compare_digest(expected_auth_header, submitted_auth):
            return Response(status=200)

        else:
            error = 'Incorrect token'
            response = {'looker': {'success': False, 'message': error}}
            print(response)
            return Response(json.dumps(response), status=403, mimetype='application/json')


# translate python to SQL datatypes for predict function
def py_type_to_sql(value):
    if value is None:
        return 'NULL'
    if type(value) == int or type(value) == float:
        return value
    if type(value) == str:
        return "'{}'".format(value)
    if type(value) == bool:
        if value == True:
            return 'TRUE'
        else:
            return 'FALSE'


def model_options(form_params):
    if 'optimize_strategy' in form_params:
        return ", OPTIMIZE_STRATEGY = '{}'".format(form_params['optimize_strategy'])
    elif 'auto_class_weights' in form_params:
        return ', AUTO_CLASS_WEIGHTS = {}'.format(form_params['auto_class_weights'])
    elif 'budget_hours' in form_params and form_params['budget_hours'].isdigit():
        return ', BUDGET_HOURS = {}'.format(float(form_params['budget_hours']))
    else:
        return ''
