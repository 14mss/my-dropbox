# my-dropbox

My Dropbox Activity: 2110524 Cloud Computing Technologies

- Build a Dropbox-like app called myDropbox using python
- Features of myDropbox
  - Upload/Download
  - Sharing
- Cloud services
  - AWS Lambda
  - Amazon S3
  - Amazon DynamoDB

## Table of contents

- [Client](#client)
- [Lambda function](#lambda-function)

#

## Client

### function `main()`

- มีการรับ input จาก user และ check condition ตาม command ที่ป้อนเข้ามา

### function `check_user_login()`

- check ว่าตอนนี้ user กำลัง login อยู่หรือไม่ โดยจะ check ก่อนเรียก `LOGGED_IN_COMMANDS` = ["view", "get", "put", "share"]

### command ต่างๆ:

- newuser:

  - check that password and confirm password are the same.
  - call function `create_user()`:
    - send request to check **if user is already existed**.
    - if not existed, get response of created user

- login:

  - call function `login()`:
    - send request to check **if username and password are correct**
    - if correct, set global variable `CURRENT_USER` to `username`

- logout:

  - set `CURRENT_USER` to `None`

- put:

  - call function `put_file()`
    - encode file to base64
    - put file and filename to S3

- view:

  - call function `get_files_info()`
    - send request to get files information

- get:

  - call function `get_file_url()`
    - send request to get pre-signed url from S3
  - call function `download_file()`
    - download file from pre-signed url to current working directory

- share:
  - call function `share_file()`
    - send request to add shared_user

## Lambda function

### dynamodb มี 2 tables คือ

1. `USERS_TABLE` = `myDropboxUsers`
2. `SHAREFILES_TABLE` = `myDropboxSharedFiles`

### command ต่างๆ:

- newuser:

  - call function `check_user_exist()`
    - if not exist, put item to `USERS_TABLE`
  - if user exist, return status 409, "User already exists"

- login:

  - call function `authenticate()`
    - check username and password in `USERS_TABLE`
    - return list of found user
  - if user name and password are incorrect, return status 401 "Username or Password is incorrect."

- view:

  - call function `get_my_file_infos()`
    - use S3 `list_objects_v2` to get your own file info
  - call function `get_shared_file_infos()`
    - use S3 `head_object` to get info of file which other user share with us

- get:

  - check if user is the owner of the file
  - if not, call function `check_file_access()`

    - check if user has an access to the file - if not, return status 403 "You do not have permission to access the file."

  - if user has an access, generate S3 pre-signed url

- put:

  - call function `s3_put_object()`
    - decode from base64
    - put object to S3

- share:
  - put shared_user and filename into `SHAREFILES_TABLE`
