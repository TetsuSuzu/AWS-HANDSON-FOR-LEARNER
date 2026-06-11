import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('users')

def lambda_handler(event, context):
    required_keys = ['id', 'name', 'email', 'age', 'address', 'tel']
    item = {key: event.get(key, '') for key in required_keys}
    table.put_item(Item=item)
    return {'message': '登録が完了しました'}
