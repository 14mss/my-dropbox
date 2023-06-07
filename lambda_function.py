import json
import boto3
import base64
from boto3.dynamodb.conditions import Key

s3 = boto3.client('s3')
BUCKET = ''                     # bucket name
URL_EXPIRES_IN = 60             # expire time in seconds for pre-signed url

dynamodb = boto3.resource('dynamodb')
usersTable = dynamodb.Table('myDropboxUsers')
shareFilesTable = dynamodb.Table('myDropboxSharedFiles')


def check_user_exist(username):
    existed_user = usersTable.query(
        KeyConditionExpression=Key('username').eq(username))['Items']
    if len(existed_user) > 0:
        return {
            'statusCode': 409,
            'body': 'User already exists.'
        }


def authenticate(username, password):
    user = usersTable.query(
        KeyConditionExpression=Key('username').eq(username) & Key('password').eq(password))['Items']
    if len(user) == 0:
        return {
            'statusCode': 401,
            'body': 'Username or Password is incorrect.'
        }
    return user


def format_file_info(key):
    file_path = key['Key'].split('/')
    owner = file_path[0]
    filename = file_path[1]
    return f"{filename} {str(key['Size'])} {key['LastModified'].strftime('%Y-%m-%d %H:%M:%S')} {owner}"


def get_my_file_infos(prefix):
    file_infos = []
    s3_response = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    if s3_response['KeyCount'] > 0:
        for key in s3_response['Contents']:
            file_infos.append(format_file_info(key))
    return file_infos


def get_shared_file_infos(username):
    file_infos = []
    shared_files = shareFilesTable.query(
        KeyConditionExpression=Key('username').eq(username))['Items']
    for shared_file in shared_files:
        key = s3.list_objects_v2(Bucket=BUCKET, Prefix=shared_file['file'])[
            'Contents'][0]
        file_infos.append(format_file_info(key))
    return file_infos


def check_file_access(username, file_path):
    shared_file = shareFilesTable.query(KeyConditionExpression=Key(
        'username').eq(username) & Key('file').eq(file_path))['Items']
    if len(shared_file) == 0:
        return {
            'statusCode': 403,
            'body': 'You do not have permission to access the file.'
        }
    return True


# For PUT FILE command
# Decode from base 64 and Put to S3
def s3_put_object(file_string, file_path):
    buffer = base64.b64decode(file_string)
    return s3.put_object(Bucket=BUCKET, Body=buffer, Key=file_path)


def lambda_handler(event, context):

    data = event

    # data = json.loads(event['body'])
    command = data['command']
    username = data['username']
    current_folder = f"{username}/"

    if command == 'newuser':
        password = data['password']
        check_user_exist(username)
        response = usersTable.put_item(
            Item={
                'username': username,
                'password': password
            })

    elif command == 'login':
        password = data['password']
        response = authenticate(username, password)

    # For VIEW command
    elif command == 'view':
        response = get_my_file_infos(
            current_folder) + get_shared_file_infos(username)

    # For GET FILE FILE_OWNER command
    # Generate pre-signed url
    elif command == 'get':
        filename = data['filename']
        owner = data['owner']
        file_path = f"{owner}/{filename}"

        if owner is not username:
            check_file_access(username, file_path)
        response = s3.generate_presigned_url('get_object', Params={
            'Bucket': BUCKET, 'Key': file_path}, HttpMethod='GET', ExpiresIn=URL_EXPIRES_IN)

    elif command == 'put':
        file_string = data['file']
        filename = data['filename']
        response = s3_put_object(file_string, current_folder+filename)

    elif command == 'share':
        shared_user = data['shared_user']
        filename = current_folder+data['filename']
        response = shareFilesTable.put_item(
            Item={
                'username': shared_user,
                'file': filename
            })

    response = str(response)

    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
