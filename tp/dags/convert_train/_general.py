from locale import D_FMT
import boto3
import botocore
import sagemaker
import sys
import pandas as pd
import convert_train.s3_conn as conn
from sagemaker.predictor import csv_serializer, json_deserializer
from io import StringIO
import os
import numpy as np


def save_df(origin, bucket, prefix, filename, df_final):
    print(df_final)
    if origin == "s3":
        csv_buffer = StringIO()
        df_final.to_csv(csv_buffer)
        # print(prefix)
        # print(filename)
        s3_object = os.path.join(prefix, "", filename)
        print(prefix)
        # print(s3_object)
        boto3.Session(
            region_name=conn.AWS_REGION,
            aws_access_key_id=conn.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=conn.AWS_SECRET_ACCESS_KEY,
            aws_session_token=conn.AWS_SESSION_TOKEN,
        ).resource("s3").Bucket(bucket).Object(s3_object).put(
            Body=csv_buffer.getvalue()
        )
    else:
        df_final.to_csv(f"{filename}")


def obtain_file(origin, file_name, bucket_obj):
    if origin == "s3":
        obj = bucket_obj.Object(key=file_name)
        response = obj.get()
        status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status != 200:
            print(f"Unsuccessful S3 get_object response. Status - {status}")
        else:
            print(f"Successful S3 get_object response. Status - {status}")
            df = pd.read_csv(response.get("Body"))
        return df
    else:
        df = pd.read_csv(file_name)
    return df
