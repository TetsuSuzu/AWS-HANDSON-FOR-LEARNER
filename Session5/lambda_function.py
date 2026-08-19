import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('users')

def lambda_handler(event, context):
    operation = event.get('operation')

    if operation == 'get_all':
        response = table.scan()
        return {'items': response.get('Items', [])}

    if operation == 'get':
        response = table.get_item(Key={'id': event['id']})
        return {'item': response.get('Item')}

    if operation == 'put':
        required_keys = ['id', 'name', 'email', 'age', 'address', 'tel']
        item = {key: event.get(key, '') for key in required_keys}
        table.put_item(Item=item)
        return {'message': '更新が完了しました'}

    if operation == 'delete':
        table.delete_item(Key={'id': event['id']})
        return {'message': '削除が完了しました'}

    return {'error': '不明な操作です'}
