import boto3
import botocore
import sagemaker
import sys
import pandas as pd
import convert_train.s3_conn as conn
import os
from sagemaker.amazon.common import numpy_to_record_serializer
from io import StringIO


def check_bucket_permission(bucket):
    # check if the bucket exists
    permission = False
    try:
        boto3.Session(
            region_name=conn.AWS_REGION,
            aws_access_key_id=conn.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=conn.AWS_SECRET_ACCESS_KEY,
            aws_session_token=conn.AWS_SESSION_TOKEN,
        ).client("s3").head_bucket(Bucket=bucket)
    except botocore.exceptions.ParamValidationError as e:
        print(
            "Hey! You either forgot to specify your S3 bucket"
            " or you gave your bucket an invalid name!"
        )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "403":
            print(f"Hey! You don't have permission to access the bucket, {bucket}.")
        elif e.response["Error"]["Code"] == "404":
            print(f"Hey! Your bucket, {bucket}, doesn't exist!")
        else:
            raise
    else:
        permission = True
    return permission


# def obtain_file(file_name, bucket_obj):
#   obj = bucket_obj.Object(key=file_name)
#    response = obj.get()
#    status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
#    df_and_avg = []
#    if status != 200:
#        print(f"Unsuccessful S3 get_object response. Status - {status}")
#       return df_and_avg

#    print(f"Successful S3 get_object response. Status - {status}")
#    df = pd.read_csv(response.get("Body"))
#    return df


def convert_and_upload_training_data(ndarray, bucket, prefix, filename="data.pbr"):

    # convert Numpy array to Protobuf RecordIO format
    serializer = numpy_to_record_serializer()
    buffer = serializer(ndarray)
    # print(buffer)

    # upload to S3
    s3_object = os.path.join(prefix, "train", filename)
    print(s3_object)
    print(bucket)

    boto3.Session(
        region_name=conn.AWS_REGION,
        aws_access_key_id=conn.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=conn.AWS_SECRET_ACCESS_KEY,
        aws_session_token=conn.AWS_SESSION_TOKEN,
    ).resource("s3").Bucket(bucket).Object(s3_object).upload_fileobj(buffer)
    s3_path = "s3://{}/{}".format(bucket, s3_object)

    print(s3_path)
    return s3_path
