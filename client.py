import requests
import json
import base64
import urllib
import os

ENDPOINT = ''  # lambda function endpoint
CURRENT_USER = None
LOGGED_IN_COMMANDS = ['view', 'get', 'put', 'share']


# Create a new user with input username and password
# If the username is already existed, print 'User already exists.'
def create_user(username, password):
    response = requests.post(ENDPOINT,
                             json={'command': 'newuser', 'username': username, 'password': password})
    if response.status_code == 200:
        print('OK')
    else:
        print(response.text)


# Login by sending a POST request to check if the user is in database
# If the username or password is incorrect, print 'Username or Password is incorrect.'
def login(username, password):
    response = requests.post(
        ENDPOINT, json={'command': 'login', 'username': username, 'password': password})
    if response.status_code == 200:
        global CURRENT_USER
        CURRENT_USER = username
        print('OK')
    else:
        print(response.text)


# Check if user is logged in
# Returns True if user is logged in, False otherwise
def check_user_login():
    global CURRENT_USER
    if CURRENT_USER is None:
        print('Please login.')
        return False
    return True


# Return List of files information
def get_files_info():
    response = requests.post(
        ENDPOINT, json={'command': 'view',  'username': CURRENT_USER})
    print('OK')
    return json.loads(response.text)


# Encode file to base 64 and Put to S3
def put_file(filename):
    uploaded_file = open(filename, 'rb').read()
    file_base64 = base64.b64encode(uploaded_file).decode('utf-8')
    requests.post(
        ENDPOINT, json={'command': 'put', 'file': file_base64, 'filename': filename, 'username': CURRENT_USER})
    print('OK')


# Return Pre-signed url of file from S3 to download
def get_file_url(filename, owner):
    response = requests.post(
        ENDPOINT, json={'command': 'get', 'filename': filename, 'owner': owner, 'username': CURRENT_USER})
    if response.status_code == 200:
        download_file(json.loads(response.text), filename)
    else:
        print(response.text)


# Download file from Pre-signed url to current working directory
def download_file(download_url, filename):
    pwd = os.path.abspath('.')
    file_path = os.path.join(pwd, filename)
    urllib.request.urlretrieve(download_url, file_path)
    print('OK')


# Share file with another user (shared_user)
def share_file(filename, shared_user):
    requests.post(
        ENDPOINT, json={'command': 'share', 'filename': filename, 'shared_user': shared_user, 'username': CURRENT_USER})
    print('OK')


def main():
    print('Welcome to myDropbox Application\n======================================================\nPlease input command (newuser username password password, login\nusername password, put filename, get filename, view, or logout).\nIf you want to quit the program just type quit.\n======================================================')
    input_command = ''

    while True:
        input_command = input('>>')
        command_list = input_command.strip().split()
        command = command_list[0]

        if command == 'newuser':
            username = command_list[1]
            password = command_list[2]
            confirm_password = command_list[3]
            if password != confirm_password:
                print('Password and Confirm Password are not the same.')
                continue
            create_user(username, password)

        elif command == 'login':
            username = command_list[1]
            password = command_list[2]
            login(username, password)

        elif command == 'logout':
            global CURRENT_USER
            CURRENT_USER = None
            print('OK')

        elif command in LOGGED_IN_COMMANDS:
            if check_user_login():
                if command == 'put':
                    put_file(command_list[1])

                elif command == 'view':
                    files_info_list = get_files_info()
                    for f in files_info_list:
                        print(f)

                elif command == 'get':
                    filename = command_list[1]
                    get_file_url(filename, command_list[2])

                elif command == 'share':
                    share_file(command_list[1], command_list[2])

        elif command == 'quit':
            print('======================================================')
            break

        else:
            print('Unknown command!')


if __name__ == '__main__':
    main()
