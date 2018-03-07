import argparse, requests
from bs4 import BeautifulSoup
import sqlite3
import os, re
import numpy as np


#-----Conection Sqlite database
def selectQuery(dbPath, query):
    conn = sqlite3.connect(dbPath)
    conn.row_factory = lambda cursor, row: row[0]
    cur = conn.cursor()
    rows = cur.execute(query).fetchall()
    return rows

def selectQueryMulti(dbPath, query):
    geolocation = []
    geolocation.append(['Lat', 'Long', 'Name'])

    conn = sqlite3.connect(dbPath)
    cur = conn.cursor()
    rows = cur.execute(query).fetchall()
    for row in rows:
        geolocation.append(list(row))
    return geolocation


#-----Interaction with Google APi

def GoogleInteraction(datos, mac):
    YOUR_API_KEY = "AIzaSyBgqJdq2ZB2wxaYyxrJBnZeFC0ytINjaUE"
    URL = "https://www.googleapis.com/geolocation/v1/geolocate?key="

    response = requests.post(URL+YOUR_API_KEY, json=datos)

    if response.status_code == 200:
        latitud = response.json()['location']['lat']
        longitud = response.json()['location']['lng']

        return [latitud, longitud, mac]
    else:
        return [40.4377317, -3.2868383999999997, '72688506']

"""
def AccesPointWifiTriangulation(bssid):
    datos = {
        "considerIp": "false",
        "wifiAccessPoints": [
            {
                "macAddress": "%s" % bssid[1],
                "signalStrength": -48,
                "signalToNoiseRatio": 0
            },
            {
                "macAddress": "%s" % bssid[2],
                "signalStrength": -49,
                "signalToNoiseRatio": 0
            }
        ]
    }

"""

#-----Diferent types of get Geolocation
def DireccionIP():
    datos = {
        "considerIp": "true"
    }
    return datos


def AccesPointWifi(bssid):
    geolocation = []

    geolocation.append(['Lat', 'Long', 'Name'])

    for mac in bssid:
        if mac is not None:
            datos = {
                "wifiAccessPoints": [
                    {
                        "macAddress": "%s" % mac,
                    }
                ]
            }
            geolocation.append(GoogleInteraction(datos, mac))

    return geolocation



def TowerCell(bssid):
    """
    #Example: 'gsm:214:03:9150:2401'

    cellId = 73628675
    locationAreaCode = 268
    mobileCountryCode = 214,
    mobileNetworkCode = 1

    gsm[0] = gsm
    gsm[1] = 214
    gsm[2] = 03
    gsm[3] = 9150
    gsm[4] = 2401
    """


    geolocation = []
    geolocation.append(['Lat', 'Long', 'Name'])

    for gsm in bssid:
        if gsm.startswith('gsm') or gsm.startswith('lte') or gsm.startswith('cdma'):
            gsm = gsm.split(":")
            datos = {
                "considerIp": "false",
                "cellTowers": [
                    {
                        "cellId": gsm[4],
                        "locationAreaCode": gsm[3],
                        "mobileCountryCode": gsm[1],
                        "mobileNetworkCode": gsm[2]
                    }
                ]
            }

            geolocation.append(GoogleInteraction(datos, gsm[4]))

    return geolocation


def outputHtml(name, arrayData):
    file = open('templates/index.html', 'r')
    text = file.read()
    geoWifi = text.replace('{{ array }}', arrayData)

    file.close()

    file = open("templates/%s.html"%name, "w")
    file.write(geoWifi)
    file.close()


if __name__ == '__main__':

    #----Queries-------
    wigleWifi = "select lastlat, lastlon, bssid from network group by bssid"

    herrevadWifi = "select bssid from local_reports group by bssid"
    herrevadCellTowerQuery = "select rowkey from lru_table group by rowkey"


    #------Argeparse------
    parser = argparse.ArgumentParser(prog='GeoForensic', description='Example with long option names', usage='python3 GeoForensic.py [options]')

    parser.add_argument('--db_path','-db', help="Path of sqlite")
    parser.add_argument('--type','-t', help="herrevad or wiglewifi")


    args = parser.parse_args()

    if not args.db_path:
        datos = DireccionIP()

    else:
        dbPath = args.db_path
        if os.path.exists(dbPath):
            if args.type == "herrevad":
                LocationBssid = AccesPointWifi(selectQuery(dbPath, herrevadWifi))
                outputHtml("herrevadWifi",str(LocationBssid))

                cellTower = TowerCell(selectQuery(dbPath, herrevadCellTowerQuery))
                outputHtml("herrevadCellTower",str(cellTower))

            elif args.type == "wiglewifi":
                LocationBssid = selectQueryMulti(dbPath, wigleWifi)
                outputHtml("wigleWifi", str(LocationBssid))

            else:
                print("No has introducido un tipo correcto")



        else:
            print("No existe la ruta")

