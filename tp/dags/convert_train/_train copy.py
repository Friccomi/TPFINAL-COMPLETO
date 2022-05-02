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


def train_model(bucket, prefix, s3_train_data, execution_role, region_name):
    containers = {
        "us-west-2": "174872318107.dkr.ecr.us-west-2.amazonaws.com/randomcutforest:latest",
        "us-east-1": "382416733822.dkr.ecr.us-east-1.amazonaws.com/randomcutforest:latest",
        "us-east-2": "404615174143.dkr.ecr.us-east-2.amazonaws.com/randomcutforest:latest",
        "eu-west-1": "438346466558.dkr.ecr.eu-west-1.amazonaws.com/randomcutforest:latest",
    }
    container = containers[region_name]

    session = sagemaker.Session(
        boto3.Session(
            region_name=conn.AWS_REGION,
            aws_access_key_id=conn.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=conn.AWS_SECRET_ACCESS_KEY,
            aws_session_token=conn.AWS_SESSION_TOKEN,
        )
    )

    rcf = sagemaker.estimator.Estimator(
        container,
        execution_role,
        output_path="s3://{}/{}/output".format(bucket, prefix),
        train_instance_count=1,
        train_instance_type="ml.c5.xlarge",
        sagemaker_session=session,
    )

    rcf.set_hyperparameters(num_samples_per_tree=200, num_trees=50, feature_dim=1)

    s3_train_input = sagemaker.session.s3_input(
        s3_train_data,
        distribution="ShardedByS3Key",
        content_type="application/x-recordio-protobuf",
    )

    rcf.fit({"train": s3_train_input})
    return rcf


def predict(rcf, bucket, prefix, filename, filename2, df):
    print("ENTRE EN PREDICT")
    print(bucket)
    print()
    rcf_inference = rcf.deploy(
        initial_instance_count=1,
        instance_type="ml.c5.xlarge",
    )

    rcf_inference.content_type = "text/csv"
    rcf_inference.serializer = csv_serializer
    rcf_inference.deserializer = json_deserializer

    cant = df.shape[0]
    cant_train = int(cant / 40000)
    cant_final = 0
    n = 0
    df_final = []
    print(df.count())
    while n <= cant_train:  # have to split df, if not is too big for sagemaker
        cant_ini = cant_final
        cant_final = cant_ini + 40000

        # print(f"cant final {cant_final}")
        train_data = df[cant_ini:cant_final].copy()
        results = rcf_inference.predict(train_data.to_numpy().reshape(-1, 1))
        scores = [datum["score"] for datum in results["scores"]]
        train_data["score"] = pd.Series(scores, index=train_data.index)
        if n == 0:
            df_final = train_data
        else:
            df_final = pd.concat([df_final, train_data])
        n = n + 1
        # print("df[" + str(cant_ini) + "- " + str(cant_final) + "]")

    print(df_final.count())
    print(df_final)

    df_score_mean_std = (
        df_final.groupby(["origin", "fl_date"])["score"].agg(["mean", "std"]).fillna(0)
    )
    print(df_score_mean_std.sort_values(["origin"]))

    df_final1 = pd.merge(
        df_final,
        df_score_mean_std,
        how="left",
        left_on=["origin", "fl_date"],
        right_on=["origin", "fl_date"],
    )
    print(df_final1.sort_values(["origin"]))
    anormales = df_final1[df_final1["score"] > df_final1["mean"] + 3 * df_final1["std"]]

    # df_final1["anormal"] = df_final1["mean"] + 3 * df_final1["std"] - df_final1["score"]
    # df_final1["anormal"] = df_final1.anormal.astype(int)
    # df_final1["anormal"] = df_final1["anormal"].abs()
    print(df_final1)
    csv_buffer = StringIO()
    df_final1.to_csv(csv_buffer)
    s3_object = os.path.join(prefix, "result", filename)
    print(prefix)
    print(s3_object)
    boto3.Session(
        region_name=conn.AWS_REGION,
        aws_access_key_id=conn.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=conn.AWS_SECRET_ACCESS_KEY,
        aws_session_token=conn.AWS_SESSION_TOKEN,
    ).resource("s3").Bucket(bucket).Object(s3_object).put(Body=csv_buffer.getvalue())

    csv_buffer = StringIO()
    anormales.to_csv(csv_buffer)
    s3_object = os.path.join(prefix, "result", filename2)
    print(prefix)
    print(s3_object)
    boto3.Session(
        region_name=conn.AWS_REGION,
        aws_access_key_id=conn.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=conn.AWS_SECRET_ACCESS_KEY,
        aws_session_token=conn.AWS_SESSION_TOKEN,
    ).resource("s3").Bucket(bucket).Object(s3_object).put(Body=csv_buffer.getvalue())
