from ast import Expression, Return
from distutils.command.build import build
import json
from typing import Type
from unittest import result
from urllib import request, response
from custom_encoder import CustomEncoder
import boto3
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
dynamodbTableName = 'product-inventory'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(dynamodbTableName)

getMethod = 'GET'
postMethod = 'POST'
patchMethod = 'PATCH'
deleteMethod = 'DELETE'
healthPath = '/health'
productPath = '/product'
productsPath = '/products'

def lambda_handler(event, context):
    logger.info(event)
    httpMethod = event['httpMethod']
    path = event['path']
    if httpMethod == getMethod and path == healthPath:
        response = buildResponse(200)
    elif httpMethod == getMethod and path == productPath:
        response = getProduct(event['queryStringParameters']['productid'])
    elif httpMethod == getMethod and path == productPath:
        response = getProducts()
    elif httpMethod == postMethod and path == productPath:
        response = saveProduct(json.loads(event['body']))
    elif httpMethod == patchMethod and path == productPath:
        requestBody = json.loads(event['body'])
        response = modifyProduct(requestBody['productId'], requestBody['updateKey'], requestBody['updateValue'] )
    elif httpMethod == deleteMethod and path == productPath:
        requestBody = json.loads(event['body'])
        response = deleteProduct(requestBody['productId'])
    else:
        response = buildResponse(404, 'Not Found')
    return response

def getProduct(productId):
    try:
        response = table.get_item(
            key = {
                'productId' == productId
            }
        )
        if 'Item' in response:
            return buildResponse(200, response['Item'])
        else:
            return buildResponse(404, {'Message': 'ProductId %s not found' %productId})

    except:
        logger.exception('Do your custom enable handling here. i am just gonna log it out here!')
def getProducts():
    try:
        response = table.scan()
        result = response['Item']

        while 'LastEvaluatedKey' in response:
            response = response.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            result.extend(response['Item'])
            
        body = {
            'products' == response
        }
                  
        return buildResponse(200, body)
    except:
        logger.exception('Do your custom enable handling here. i am just gonna log it out here!')

def saveProduct(requestBody):
    try:
        table.put_item(Item=requestBody)
        body = {
            'Operation' : 'SAVE',
            'Message' : 'SUCCESS',
            'Item' : requestBody
        }
        return buildResponse(200, body)
    except:
        logger.exception('Do your custom enable handling here. i am just gonna log it out here!')
def modifyProduct(productId, updateKey, updateValue):
    try:
        response = table.update_item(
            key = {
                'productId' : productId
            },
            UpdateExpressions='set %s = :value' % updateKey,
            ExpressionAttributeValues={
                'value' : updateValue
            },
            ReturnValues='UPDATED_NEW'
        )
        body = {
            'Operation' : 'UPDATE',
            'Message' : 'SUCCESS',
            'UpdatedAttributes' : response
        }
        return buildResponse(200, body)
    except:
        logger.exception('Do your custom enable handling here. i am just gonna log it out here!')
def deleteProduct(productId):
    try:
        response = table.delete_item(
            key={
                'productId' : productId
            },
            ReturnValues='ALL_OLD'
        )
        body = {
            'Operation' : 'DELETE',
            'Message' : 'SUCCESS',
            'deletedItem' : response
        }
        return buildResponse(200, body)
    except:
        logger.exception('Do your custom enable handling here. i am just gonna log it out here!')

def buildResponse(statusCode, body = None):
    response = {
        'statusCode' : statusCode,
        'headers' : {
            'Content-Type' : 'application/json',
            'Access-Control-Allow-Origin' : '*'
        }
    }
    if body is not None:
        response['body'] = json.dumps(body, cls = CustomEncoder)
    return response