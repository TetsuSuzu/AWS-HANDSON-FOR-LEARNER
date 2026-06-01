import json
import boto3

bedrock_runtime_client = boto3.client(service_name='bedrock-runtime', region_name='us-east-1')

def lambda_handler(event, context):
    user_prompt = event["key1"]
    model_id = 'global.anthropic.claude-sonnet-4-6'
    system_prompt = "あなたは生成AIのエージェントです。ユーザからの質問に丁寧に回答してください。"
    max_tokens = 1000
    temperature = 0

    user_message = {
        "role": "user",
        "content": user_prompt      
    }
    body = json.dumps(
        {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [user_message],
        "temperature": temperature
        }  
    )  

    response = bedrock_runtime_client.invoke_model(body=body, modelId=model_id)
    response_json = json.loads(response.get('body').read())
    
    return response_json['content'][0]['text']