import json
import os
import re
import time
from flask import Response
from google.cloud import bigquery
from icon import icon_data_uri
from utils import authenticate, py_type_to_sql, model_options
client = bigquery.Client()


BASE_DOMAIN = 'https://{}-{}.cloudfunctions.net/{}-'.format(os.environ.get(
    'REGION'), os.environ.get('PROJECT'), os.environ.get('ACTION_NAME'))


# https://github.com/looker-open-source/actions/blob/master/docs/action_api.md#actions-list-endpoint
def action_list(request):
    """Return action hub list endpoint data for action"""
    auth = authenticate(request)
    if auth.status_code != 200:
        return auth

    response = {
        'integrations': [{
            'name': os.environ.get('ACTION_NAME'),
            'label': os.environ.get('ACTION_LABEL'),
            'supported_action_types': ['query'],
            "icon_data_uri": icon_data_uri,
            'form_url': BASE_DOMAIN + 'form',
            'url': BASE_DOMAIN + 'execute',
            'supported_formats':['json_detail'],
            'supported_formattings':['unformatted'],
            'supported_visualization_formattings': ['noapply'],
            'params': [
                {'name': 'email', 'label': 'Email',
                    'user_attribute_name': 'email', 'required': True},
                {'name': 'user_id', 'label': 'User ID',
                    'user_attribute_name': 'id', 'required': True}
            ]
        }]
    }

    print('returning integrations json')
    return Response(json.dumps(response), status=200, mimetype='application/json')


# https://github.com/looker-open-source/actions/blob/master/docs/action_api.md#action-form-endpoint
def action_form(request):
    """Return form endpoint data for action"""
    auth = authenticate(request)
    if auth.status_code != 200:
        return auth

    request_json = request.get_json()
    form_params = request_json['form_params']
    print(form_params)

    # step 1 - select a model type
    response = [{
        'name': 'model_type',
        'label': 'Model Selection',
        'description': "Choose your objective. Select 'Regression' to train a model to predict numeric values. Select 'classification' to train a model to predict a class or category.",
        'type': 'select',
        'required': True,
        'options': [
                {'name': 'AUTOML_CLASSIFIER',
                    'label': 'AutoML Classification (AUTOML_CLASSIFIER)'},
                {'name': 'AUTOML_REGRESSOR',
                    'label': 'AutoML Regression (AUTOML_REGRESSOR)'},
                {'name': 'LOGISTIC_REG',
                    'label': 'Logistic Classification (LOGISTIC_REG)'},
                {'name': 'LINEAR_REG',
                    'label': 'Linear Regression (LINEAR_REG)'},
        ],
        'interactive': True  # dynamic field for model specific options
    }]

    # step 2 - select model type specific parameters
    if 'model_type' in form_params:
        if form_params['model_type'] == 'LINEAR_REG':
            response.extend([{
                'name': 'optimize_strategy',
                'label': 'Optimize Strategy',
                'description': 'The strategy to train linear regression models.',
                'type': 'select',
                'required': True,
                'default': 'AUTO_STRATEGY',
                'options': [{'name': 'AUTO_STRATEGY',
                             'label': 'Auto Strategy'},
                            {'name': 'BATCH_GRADIENT_DESCENT',
                                'label': 'Batch Gradient Descent'},
                            {'name': 'NORMAL_EQUATION',
                                'label': 'Normal Equation'}]
            }])
        if form_params['model_type'] == 'LOGISTIC_REG':
            response.extend([{
                'name': 'auto_class_weights',
                'label': 'Auto Class Weights',
                'description': 'Whether to balance class labels using weights for each class in inverse proportion to the frequency of that class.',
                'type': 'select',
                'required': True,
                'default': 'False',
                'options': [{'name': True, 'label': 'True'},
                            {'name': False, 'label': 'False'}]
            }])
        if 'AUTOML' in form_params['model_type']:
            response.extend([{
                'name': 'budget_hours',
                'label': 'Budget Hours',
                'required': True,
                'default': '1',
                'description': 'Enter the maximum number of hours to train the model (must be between 1 and 72)',
                'type': 'text',
            }])

        # step 3 - specify model name, identifier column, and target column
        response.extend([
            {
                'name': 'model_name',
                'label': 'Model Name',
                'description': 'Model names can only contain letters, numbers, and underscores.',
                'type': 'text',
                'required': True,
            },
            {
                'name': 'identifier_column',
                'label': 'Enter your ID column',
                'description': 'Enter the column name of the row identifier to be excluded from the model input.',
                'type': 'text',
                'required': True,
            },
            {
                'name': 'target_column',
                'label': 'Enter your target',
                'description': 'Enter the column name to train the model on.',
                'type': 'text',
                'required': True,
            }
        ])

    print('returning form json: {}'.format(json.dumps(response)))
    return Response(json.dumps(response), status=200, mimetype='application/json')


# https://github.com/looker-open-source/actions/blob/master/docs/action_api.md#action-execute-endpoint
def action_execute(request):
    """Create BigQuery ML model from a Looker action"""
    auth = authenticate(request)
    if auth.status_code != 200:
        return auth

    request_json = request.get_json()
    attachment = request_json['attachment']
    action_params = request_json['data']
    form_params = request_json['form_params']
    print(action_params)
    print(form_params)

    # create model query (sql_query with idenfier is also used for view creation)
    data = json.loads(attachment['data'])
    # remove comments and new lines
    sql_query = re.sub(r'--.*', '', data['sql']).replace('\n', ' ')
    sql_query = re.sub(r'LIMIT \d+', '', sql_query)  # remove row limit
    cleaned_sql_query = 'SELECT * EXCEPT ({}) FROM ({})'.format(
        form_params['identifier_column'], sql_query)  # remove row identifier from model input
    extra_options = model_options(form_params)  # model specific params

    sql_create = """CREATE OR REPLACE MODEL {}.model_{}
                    OPTIONS(MODEL_TYPE='{}'
                    , INPUT_LABEL_COLS = ['{}']
                    {})
                    AS {}""".format(os.environ.get('DATASET'), form_params['model_name'], form_params['model_type'], form_params['target_column'], extra_options, cleaned_sql_query)
    print(sql_create.replace('\n', ' '))

    bq_job = client.query(sql_create)
    time.sleep(60)  # wait a minute to check for errors
    bq_status = client.get_job(job_id=bq_job.job_id, project=bq_job.project,
                               location=bq_job.location)
    print(bq_status)

    if bq_status.error_result != None:
        error = 'Error with query to create BigQuery model: {}'.format(
            bq_status.error_result['message'])
        print(error)
        response = {'looker': {'success': False, 'message': error}}
        return Response(json.dumps(response), status=400, mimetype='application/json')
    else:
        print('No errors creating BigQuery model')

        # create sql view for query to use for predictions
        sql_view = """CREATE VIEW {}.view_{} AS ({})""".format(
            os.environ.get('DATASET'), form_params['model_name'], sql_query)
        print(sql_view)
        client.query(sql_view)
        print('View for query created')

        # add metadata on bigquery model to bqml_models table
        sql_insert = """INSERT {}.bqml_models (model_name, created_at, model_type, target_column, sql_text)
                        VALUES('{}', CURRENT_TIMESTAMP(), '{}', '{}', '''{}''')""".format(os.environ.get('DATASET'), form_params['model_name'], form_params['model_type'], form_params['target_column'], sql_create)
        print(sql_insert.replace('\n', ' '))
        client.query(sql_insert)
        print('Model info added to bqml_models table')

    return Response(status=200, mimetype='application/json')


# expected input json object:
# {
#     "model_name": "my_bqml_model_name",
#     "columns": {
#             "customers_city": "London",
#             "order_items_average_basket_value": 250,
#             "order_items_average_basket_size": 1.456,
#             "order_items_has_returns": false,
#             "order_items_total_returns": null
#             ...
#     }
# }
def predict(request):
    """Returns prediction for input"""
    auth = authenticate(request)
    if auth.status_code != 200:
        return auth

    request_json = request.get_json()
    select_columns = ', '.join(["{} AS {}".format(py_type_to_sql(
        value), key) for key, value in request_json['columns'].items()])
    sql_predict = """SELECT * FROM ML.PREDICT(
                    MODEL `{}.{}`, (SELECT {}))""".format(os.environ.get('DATASET'), request_json['model_name'], select_columns)
    bq_job = client.query(sql_predict)

    if bq_job.error_result != None:
        query_error = 'Error with prediction query: {}'.format(
            bq_job.error_result['message'])
        print(query_error.replace('\n', ' '))
        return Response(json.dumps(query_error), status=400, mimetype='application/json')

    records = [dict(row) for row in bq_job.result()]
    return Response(json.dumps(records), status=200, mimetype='application/json')
