#!/usr/bin/python3
import neopixel
import time

class WeatherDevice:
    def __init__(self, neoPixel):
        self.epoch = 0
        self.p = neoPixel
        self.temp = 200
        self.prevTemp = 200 #so it doesn't write the prev temp the first time
        self.wind = 0
        self.prevWind = 0
        self.windDir = 0
        self.prevWindDir = 0
        self.gust = 0
        self.gustList = [0]
        self.maxGust = 0
        self.baro = 0
        self.prevBaro = 0
        self.rainAmt = 0
        self.rainTotal = 0
        self.velocity = 0
        
        

        
    def getWindDir(self, wind_dir):
        if wind_dir > 348:
            wind_dir = ("N",0)
        elif wind_dir > 326:
            wind_dir = ("NNW", 23)
        elif wind_dir > 303:
            wind_dir = ("NW",22)
        elif wind_dir > 281:
            wind_dir = ("WNW", 19)
        elif wind_dir > 258:
            wind_dir = ("W",18)
        elif wind_dir > 236:
            wind_dir = ("WSW",17)
        elif wind_dir > 213:
            wind_dir = ("SW",15)
        elif wind_dir > 191:
            wind_dir = ("SSW",14)
        elif wind_dir > 168:
            wind_dir = ("S",12)
        elif wind_dir > 146:
            wind_dir = ("SSE",10)
        elif wind_dir > 123:
            wind_dir = ("SE",9)
        elif wind_dir > 101:
            wind_dir = ("ESE",7)
        elif wind_dir > 78:
            wind_dir = ("E",6)
        elif wind_dir > 56:
            wind_dir = ("ENE",4)
        elif wind_dir > 33:
            wind_dir = ("NE",3)
        elif wind_dir > 11:
            wind_dir = ("NNE",2)
        else:
            wind_dir = ("N",0)

        return wind_dir
        
    
        
