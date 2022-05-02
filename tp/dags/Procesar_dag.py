"""Stocks dag extended."""
import os
from pathlib import Path

from pendulum import YEARS_PER_CENTURY

PYTHONPATH = "PYTHONPATH"
try:
    pythonpath = os.environ[PYTHONPATH]
    print(pythonpath)
except KeyError:
    pythonpath = ""
# print("BEFORE:", pythonpath)
folder = Path(__file__).resolve().parent.joinpath("convert_train")
# print(f"{folder=}")
pathlist = [str(folder)]
if pythonpath:
    pathlist.extend(pythonpath.split(os.pathsep))
#    print(f"{pathlist=}")
os.environ[PYTHONPATH] = os.pathsep.join(pathlist)
# print("AFTER:", os.environ[PYTHONPATH])


from ast import Pass
import json
from datetime import datetime
from os import ctermid
from time import sleep
import numpy as np
import pandas as pd
import requests  # type: ignore

import sqlalchemy


from airflow.providers import postgres
from airflow.models import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator
from airflow.operators.postgres_operator import PostgresOperator
from sqlPostgresCli import SqlPostgresClient
from decouple import config
import matplotlib.pyplot as plt

import csv
import boto3
import convert_train.s3_conn as conn
from io import StringIO
import sagemaker.amazon.common
import convert_train._convert as conv
import convert_train._train as train
import matplotlib.pyplot as plt
import convert_train._graphics as graf
import convert_train._general as grl
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float

SCHEMA = config("DB_SCHEMA")
print(SCHEMA)

destiny = conn.destiny
origin = conn.origin
if origin == "s3":
    s3 = boto3.resource(
        service_name="s3",
        region_name=conn.AWS_REGION,
        aws_access_key_id=conn.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=conn.AWS_SECRET_ACCESS_KEY,
        aws_session_token=conn.AWS_SESSION_TOKEN,
    )
    bucket_name = conn.AWS_BUCKET_NAME
    bucket = s3.Bucket(bucket_name)
    bucket_obj = s3.Bucket(bucket_name)
    execution_role = conn.AWS_EXECUTION_ROLE
    region = conn.AWS_REGION
else:
    s3 = ""
    bucket_name = ""
    bucket = ""
    region = ""

prefix = "sagemaker/rcf-benchmarks"
path_name = "tp/"


def _clean_s3_dir(path, **context):
    date = context["logical_date"]
    date = date.date()
    year = date.strftime("%Y")  # read execution date from context

    s3.Object(bucket_name, path + f"tp_avgs/{year}_avg.csv").delete()
    bucket.objects.filter(Prefix=path + f"result/{year}").delete()
    bucket.objects.filter(Prefix=path + f"graphics/{year}").delete()


def _calculate_mean_delay(path, **context):
    date = context["logical_date"]
    date = date.date()
    year = date.strftime("%Y")  # read execution date from context
    #year = f"{context['execution_date']:%Y}"  # read execution date from context
    file_name = path + f"{year}.csv"
    print("ACA")
    print(f"{file_name}")
    df_and_avg = []
    df_fl = grl.obtain_file(origin, file_name, bucket_obj)
    df00 = df_fl[["ORIGIN", "FL_DATE", "DEP_DELAY"]]
    df0 = df00.dropna(subset=["DEP_DELAY"])
    # print(df0)
    df0 = df0.rename(
        columns={"ORIGIN": "origin", "FL_DATE": "fl_date", "DEP_DELAY": "dep_delay"}
    )
    df0["delay"] = df0.apply(
        lambda row: row["dep_delay"] if row["dep_delay"] > 0 else 0, axis=1
    )
    df1 = df0.groupby(["origin", "fl_date"])["delay"].mean().reset_index()
    df1 = df1.rename(columns={"delay": "dep_delay_avg"})

    df_and_avg = pd.merge(
        df0,
        df1,
        how="left",
        left_on=["origin", "fl_date"],
        right_on=["origin", "fl_date"],
    )
    # print(df_and_avg.isna().any())
    # print(df_and_avg)
    df1 = df_and_avg
    prefix1 = path + "tp_avgs/"
    filename = f"{year}_avg.csv"
    grl.save_df(destiny, bucket_name, prefix1, filename, df1)
    print("grabe ")


def _search_unnormals(path, **context):
    date = context["logical_date"]
    date = date.date()
    year = date.strftime("%Y")  # read execution date from context

    downloaded_data_bucket = bucket_name
    downloaded_data_prefix = "datasets/tabular/anomaly_benchmark_flyte"
    prefix = f"sagemaker/randomcutforest_{year}"
    print(prefix)
    if conv.check_bucket_permission(bucket_name):
        print(f"Training input/output will be stored in: s3://{bucket_name}/{prefix}")
    if conv.check_bucket_permission(downloaded_data_bucket):
        print(
            f"Downloaded training data will be read from s3://{downloaded_data_bucket}/{downloaded_data_prefix}"
        )
    print("ACA2")
    file_name = path + f"tp_avgs/{year}_avg.csv"
    print(f"{file_name}")
    df = grl.obtain_file(origin, file_name, bucket_obj)

    uniqueOrigin = df["origin"].unique()
    df_airport = pd.DataFrame(uniqueOrigin, columns=["airport"])
    # print(df_airport)
    filename = f"airports_{year}.csv"
    prefix1 = path + f"result/{year}/"

    grl.save_df(origin, bucket_name, prefix1, filename, df_airport)
    print("ACA3")

    i = 0
    for air in uniqueOrigin:
        i = i + 1
        print(air)
        df1 = df.loc[(df["origin"] == air)]
        filename = f"data_{air}_{year}.pbr"
        s3_train_data = conv.convert_and_upload_training_data(
            df1.delay.to_numpy().reshape(-1, 1), bucket_name, prefix, filename
        )
        print(s3_train_data)
        rcf = train.train_model(
            bucket_name, prefix1, s3_train_data, execution_role, region
        )
        df_final = train.predict(rcf, bucket_name, path, df1)
        prefix1 = path + f"result/{year}/"
        filename = f"{air}_{year}_result.csv"
        df_final_complete = train.save_results(
            destiny, bucket_name, prefix1, filename, df_final
        )


def _generate_graphics(path, **context):
    date = context["logical_date"]
    date = date.date()
    year = date.strftime("%Y")  # read execution date from context
    filename = path + f"result/{year}/airports_{year}.csv"
    print(filename)
    df_airports = grl.obtain_file(origin, filename, bucket_obj)

    prefix = path + f"graphics/{year}"

    airports = df_airports.airport.unique()
    # airport = ["LGA"]

    for row in airports:
        airport_name = row
        filename = path + f"result/{year}/{airport_name}_{year}_result.csv"
        print(filename)
        df = grl.obtain_file(origin, filename, bucket_obj)

        df1 = df[(df["origin"] == airport_name)]
        filename = f"{airport_name}_{year}.jpg"
        print(filename)
        df_subtotals = graf.graphic(bucket_name, prefix, airport_name, df1, year, s3)
        # print(df_subtotals)
        if df_subtotals.shape[0] > 0:
            prefix1 = path + f"result/{year}/"
            filename = f"SubTot{airport_name}{year}.csv"
            # print(prefix1)
            # print(filename)
            grl.save_df(destiny, bucket_name, prefix1, filename, df_subtotals)
        else:
            print(f"No Final Data for: {year}")


def _create_delete_table(path, **context):
    date = context["logical_date"]
    date = date.date()
    year = date.strftime("%Y")  # read execution date from context
    sql_cli = SqlPostgresClient()
    engine = sql_cli._connect()

    meta = MetaData()
    aux = Table(
        f"flights_delay{year}",
        meta,
        Column("origin", String, primary_key=True),
        Column("fl_date", String, primary_key=True),
        Column("number_flight", Integer),
        Column("anormal", Integer),
        Column("number_anormals", Integer),
    )
    meta.create_all(engine)
    try:  # if table pre-exist, delete all data
        sql_cli.execute(f"truncate table flights_delay{year}")
    except sqlalchemy.exc.IntegrityError as error:
        print(str(error.orig) + " for parameters" + str(error.params))


def _save_in_DB(path, **context):
    date = context["logical_date"]
    date = date.date()
    year = date.strftime("%Y")  # read execution date from context
    filename = path + f"result/{year}/airports_{year}.csv"
    print(filename)
    df_airports = grl.obtain_file(origin, filename, bucket_obj)
    airports = df_airports.airport.unique()
    # airport = ["LGA"]
    for row in airports:
        airport_name = str(row)
        print(airport_name)
        filename = path + f"result/{year}/SubTot{airport_name}{year}.csv"
        df = grl.obtain_file(origin, filename, bucket_obj)
        df["origin"] = airport_name
        df1 = df[["origin", "fl_date", "number_flight", "anormal", "number_anormals"]]

        # print(df1)
        SQL_TABLE = f"flights_delay{year}"
        sql_cli = SqlPostgresClient()
        try:
            sql_cli.insert_from_frame(df1, SQL_TABLE)
            print(f"Inserted {len(df1)} records")
        except sqlalchemy.exc.IntegrityError:
            # You can avoid doing this by setting a trigger rule in the reports operator
            print("Data already exists! Nothing to do...")


 if __name__ == "__main__":
# _clean_s3_dir("tp/")
#  prefix1 = format(os.getcwd()) + "/tp/"
 _calculate_mean_delay("tp/")
# _search_unnormals("tp/")
# _generate_graphics("tp/")
# _create_delete_table("tp/")
# _save_in_DB("tp/")


default_args = {
    "owner": "flor",
    "retries": 0,
    "start_date": datetime(2009, 1, 1),
    "end_date": datetime(year=2011, month=1, day=1),
}

with DAG(
    "TP-FINAL",
    default_args=default_args,
    schedule_interval="@yearly",
) as dag:
    create_schema = PostgresOperator(
        task_id="Create_schema_if_not_Exists",
        sql="sql/create_env.sql",
        postgres_conn_id=config("CONN_ID"),
   )

    clean_s3_dir = PythonOperator(
       task_id="Clean_s3_dir",
       python_callable=_clean_s3_dir,
       op_kwargs={"path": "tp/"},
       provide_context=True,
   )
    calculate_mean_delay = PythonOperator(
       task_id="Calculate_mean_delays",
       python_callable=_calculate_mean_delay,
       op_kwargs={"path": "tp/"},
       provide_context=True,
   )
    search_unnormals = PythonOperator(
       task_id="Search_unnormals",
       python_callable=_search_unnormals,
       op_kwargs={"path": "tp/"},
       provide_context=True,
    )
    generate_graphics = PythonOperator(
        task_id="Generate_grafics",
        python_callable=_generate_graphics,
        op_kwargs={"path": "tp/"},
        provide_context=True,
    )
    create_delete_table = PythonOperator(
        task_id="Create_delete_table",
        python_callable=_create_delete_table,
        op_kwargs={"path": "tp/"},
        provide_context=True,
    )
    save_in_DB = PythonOperator(
        task_id="Save_in_DB",
        python_callable=_save_in_DB,
        op_kwargs={"path": "tp/"},
        provide_context=True,
    )

    (
        clean_s3_dir
        >> calculate_mean_delay
        >> search_unnormals
        >> generate_graphics
        >> create_delete_table
        >> save_in_DB
    )
