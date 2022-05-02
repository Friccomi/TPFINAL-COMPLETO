import matplotlib.pyplot as plt
from matplotlib.figure import Figure as FigureCanvas
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
import numpy as np
import io
import os
import pandas as pd


def graphic(bucket, prefix, airport, df, year, s3):
    plt.rcParams["figure.figsize"] = (25, 7)
    fig, (ax1, ax2) = plt.subplots(2, sharey=True)
    fig.subplots_adjust(hspace=1)
    plt.title(f"Number of Flights on Airport: {airport} ")

    ax1.set_xlim([0, 10])
    ax2.set_xlim([0, 10])
    vuelos_diarios = df.groupby(["fl_date"])["origin"].count().reset_index()
    vuelos_diarios = vuelos_diarios.rename(columns={"origin": "number_flight"})
    date1 = f"{year}-06-30"
    date2 = f"{year}-07-01"
    vuelos1 = vuelos_diarios[(vuelos_diarios["fl_date"] <= date1)]
    vuelos2 = vuelos_diarios[(vuelos_diarios["fl_date"] >= date2)]

    ax1.title.set_text(f"Number of Flights on Airport: {airport} until {date1}")
    ax2.title.set_text(
        f"Number of Flights on Airport: {airport} from {date1} to {date2}"
    )

    ax1.title
    ax1.plot(vuelos1["fl_date"], vuelos1["number_flight"], color="C0")
    ax1.set_ylabel("Number of Flights", color="C0")
    ticks_loc = ax2.get_yticks().tolist()
    ax1.tick_params("y", colors="C0")
    ax1.set_xticks(vuelos1["fl_date"])
    ax1.set_xticklabels(vuelos1["fl_date"], rotation="vertical", size=8)

    ax2.plot(vuelos2["fl_date"], vuelos2["number_flight"], color="C0")
    ax2.set_ylabel("Number of Flights", color="C0")
    ax2.tick_params("y", colors="C0")
    ax2.set_xticks(vuelos2["fl_date"])
    ax2.set_xticklabels(vuelos2["fl_date"], rotation="vertical", size=8)

    df2 = df[(df["anormal_day"] == 1)]
    cant_anormal = df2.shape[0]
    #print(cant_anormal)
   
    if cant_anormal > 0:
        anormal = df2.groupby(["fl_date"])["anormal_day"].sum().reset_index()
        anormal = anormal.rename(columns={"anormal_day": "number_anormals"})
        anormal["anormal"] = anormal.apply(
            lambda row: 1 if row["number_anormals"] > 0 else "0", axis=1
        )
        anormal1 = anormal[(anormal["fl_date"] <= date1)]
        anormal2 = anormal[(anormal["fl_date"] >= date2)]
        ax1.scatter(anormal1["fl_date"], anormal1["anormal"], color="red")
        ax2.scatter(anormal2["fl_date"], anormal2["anormal"], color="red")
    # plt.show()
    # fig.savefig(f"{airport}_{year}.jpg")

    plt.plot
    img_data = io.BytesIO()
    plt.savefig(img_data, format="jpg")

    filename = f"{prefix}/{airport}_{year}.jpg"
    print(filename)
    bucket_save = s3.Bucket(bucket)
    bucket_save.put_object(
        Body=img_data.getvalue(), ContentType="image/jpg", Key=filename
    )
    s3.ObjectAcl(bucket, filename).put(ACL="public-read")
    plt.close("all")

    df_subtotal = pd.merge(
        vuelos_diarios,
        anormal,
        how="left",
        left_on=["fl_date"],
        right_on=["fl_date"],
    )
    df_subtotal["anormal"] = df_subtotal["anormal"].fillna(0)
    df_subtotal["number_anormals"] = df_subtotal["number_anormals"].fillna(0)
    #print(df_subtotal)
    return df_subtotal
