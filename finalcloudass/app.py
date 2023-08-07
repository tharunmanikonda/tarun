from flask import Flask, render_template, request, session
import pymysql
import boto3

app = Flask(__name__)

app.secret_key = "given super key"
@app.route('/')
def hello(): 
    return render_template("singup.html")

given_db_name = "defaultdb"
given_db_user = "admin"
given_db_password = "multiweekdb"
given_db_port = "3306"
given_db_endpoint = "multiweekdb.clnopyq3sfwe.us-east-1.rds.amazonaws.com"


def special(password):
    flag = 0
    for i in password:
        if i in "$%&.@": 
            flag = 1
    return flag

@app.route('/signup', methods=['POST','GET'])
def signup():
    heading = "Error while Singing Up. Error Details"
    if request.method == 'POST':
        given_email = request.form['emailid']
        given_password = request.form['password']
        confirm_password = request.form['cpassword']
        if (given_password != confirm_password) or (len(given_password)<5) or (special(given_password) == 0):
            error = ["Please check both the passwords", "Passoword must be greather than 5 characters", "Password must contain special charecters like .#$%&@"]
            heading = "Password Rules"
            return render_template("error.html", error=error, headings=heading)
        try:
            table_connect = pymysql.connect(host=given_db_endpoint, user=given_db_user, password=given_db_password, database=given_db_name)
            table_cursor = table_connect.cursor()
            query = "INSERT INTO tharunusertable (Emailid, Password) VALUES (%s, %s);"
            given_data = (given_email, given_password)
            table_cursor.execute(query, given_data)
            table_connect.commit()
            table_connect.close()
            return render_template("singup.html", success = "Account Creating Succesfully")
        except Exception as error:
            heading = "Error while Inserting user Details. Error Details  "
            return render_template("error.html", error=[error], headings=heading)


@app.route('/signin', methods=['POST','GET'])
def signin():
    heading = "Error while Retriving Up. Error Details"
    if request.method == 'POST':
        given_email = request.form['emailid']
        given_password = request.form['password']
        try:
            table_connect = pymysql.connect(host=given_db_endpoint, user=given_db_user, password=given_db_password, database=given_db_name)
            table_cursor = table_connect.cursor()
            query = " SELECT Password FROM tharunusertable WHERE Emailid = %s"
            given_data = (given_email) 
            table_cursor.execute(query, given_data)
            pass_from_table = table_cursor.fetchone()
            table_connect.close()
            print(pass_from_table)
            if pass_from_table and pass_from_table[0] == given_password:
                session['user'] = given_email
                return render_template("fileupload.html", success = "You logged in succesfully..")
            else:
                return render_template("error.html", error=["Check your password"], headings=heading)

        except Exception as error:
            heading = "Error while Retriving Data. Error Details "
            return render_template("error.html", error=[error], headings=heading)
   
    return render_template("singin.html")


AccessKey = 'AKIAV4G2HHPTBJIUM7SP'
SecreatKey  = '4NrLVuvyGp8o6Znuxqv3tVubket4SqWUTynyRcrw'

def Subscribe(TopicARN, Protocol, EndPoint):
    SNS_Client = boto3.client('sns', aws_access_key_id=AccessKey, aws_secret_access_key=SecreatKey, region_name='us-east-1')

    joinSubscription = SNS_Client.subscribe(TopicArn = TopicARN, Protocol=Protocol, Endpoint=EndPoint, ReturnSubscriptionArn=True)
    return joinSubscription['SubscriptionArn']

def upload(file, user):
    try:
        table_connect = pymysql.connect(host=given_db_endpoint, user=given_db_user, password=given_db_password, database=given_db_name)
        table_cursor = table_connect.cursor()
        query = "INSERT INTO tharunbillingtable (Emailid, File) VALUES (%s, %s);"
        given_data = (user, file)
        table_cursor.execute(query, given_data)
        table_connect.commit()
        table_connect.close()
        return 1
    except Exception:
        return 0
    
@app.route('/billing')
def billing():
    table_connect = pymysql.connect(host=given_db_endpoint, user=given_db_user, password=given_db_password, database=given_db_name)
    table_cursor = table_connect.cursor()
    query = " SELECT * From tharunbillingtable "
    table_cursor.execute(query)
    files = table_cursor.fetchall()
    table_connect.close()
    return render_template("billing.html", files=files)
    
@app.route('/fileupload', methods=['POST','GET'])
def fileupload():
    if request.method == 'POST':
        try:
            given_file = request.files['givenfile']
            fileName = given_file.filename
            S3_Bucket = boto3.client('s3', aws_access_key_id = AccessKey, aws_secret_access_key=SecreatKey, region_name='us-east-1')
            S3_Bucket.upload_fileobj(given_file, "mygivenbucket", fileName)
            expiration_time = 1000
            generatedUrl = S3_Bucket.generate_presigned_url('get_object', Params={'Bucket': 'mygivenbucket', 'Key': fileName}, ExpiresIn=expiration_time)
            SNS_Client = boto3.client('sns',aws_access_key_id = AccessKey, aws_secret_access_key=SecreatKey, region_name='us-east-1')
            notification_topic = SNS_Client.create_topic(Name="givenTopic")
            user_one_email = request.form['emailid1']
            user_two_email = request.form['emailid2']
            user_three_email = request.form['emailid3']
            user_four_email = request.form['emailid4']
            user_five_email = request.form['emailid5']
            given_email_ids = [user_one_email, user_two_email, user_three_email, user_four_email, user_five_email]
            for user_email_id in given_email_ids:
                if len(user_email_id) > 1:
                    Arn = notification_topic['TopicArn']
                    protocol = 'email'
                    endpoint = user_email_id
                    response = Subscribe(Arn, protocol, endpoint)
                    SNS_Client.publish(TopicArn = Arn, Subject = "Click the link to download file ", Message = generatedUrl)
            fileuploader = upload(fileName, session['user'])
            if fileuploader == True:
                table_connect = pymysql.connect(host=given_db_endpoint, user=given_db_user, password=given_db_password, database=given_db_name)
                table_cursor = table_connect.cursor()
                query = " SELECT * From tharunbillingtable "
                table_cursor.execute(query)
                files = table_cursor.fetchall()
                table_connect.close()
                return render_template("billing.html", success = 'Upload to S3 Cloud Bucket Succesfully and A Mail was Sent', files=files)
            if fileuploader == False:
                return render_template("fileupload.html", error = 'Something Happend while uploading or Inserting Billing..')
        except Exception as e:
            print(e)
            return render_template("fileupload.html", error = 'Something Happend while uploading or Inserting Billing..')
    else:
        return render_template("fileupload.html")



if __name__ == "__main__":
    app.run(debug=True)