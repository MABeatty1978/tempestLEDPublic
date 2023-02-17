#!/usr/bin/python3
import machine, neopixel
import network
import socket
import select
import json
import time
import config
import uasyncio
import weatherDevice
import random
import math
import _thread

NUM_LED = 150
windOffset = 30
tempOffset = 50
LIGHTNING_OFFSET = 60
RAIN_OFFSET = 100
maxGustMin = 10 * 20 #There will be (should) 20 calls per minute.
dayNum = -1


#colors
clear =(0,0,0)
redH = (255,0,0)
redM = (70,0,0)
redL = (5,0,0)
blueH = (0,0,255)
blueM = (0,0,70)
blueL = (0,0,5)
greenH = (0,255,0)
greenM = (0,70,0)
greenL = (0,5,0)
whiteH = (255,255,255)
whiteM = (70,70,70)
whiteL = (5,5,5)
fuchsia = (10,0,10)

def connect(n):
    #Connect to WLAN
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config.SSID, config.PASSWD)
    
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        for x in range(24):
            n[x] = blueL
            n.write()
            time.sleep(.04)
        n.fill(clear)
        n.write()
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip

def initFlash(n):
    n.fill(redL)
    n.write()
    time.sleep(.5)
    n.fill(greenL)
    n.write()
    time.sleep(.5)
    n.fill(blueL)
    n.write()
    time.sleep(.5)
    n.fill(clear)
    n.write()
    
def setBaro(w):
    x = 26
    if w.baro > 30.2:
        
        #high pressure
        if w.baro > w.prevBaro:
            w.p[x-1] = (blueL)
            w.p[x] = (blueM)
            w.p[x+1] = (blueH)
        elif w.baro < w.prevBaro:
            w.p[x+1] = (blueL)
            w.p[x] = (blueM)
            w.p[x-1] = (blueH)
        else:
            w.p[x-1] = w.p[x] =w.p[x+1] = (blueH)
    elif w.baro < 29.8:
        #low pressure
        if w.baro > w.prevBaro:
            w.p[x-1] = (redH)
            w.p[x] = (redM)
            w.p[x+1] = (redL)
        elif w.baro < w.prevBaro:
            w.p[x+1] = (redH)
            w.p[x] = (redM)
            w.p[x-1] = (redL)
        else:
            w.p[x+1] = w.p[x] =w.p[x-1] = (redH)
    else:
        #normal pressure
        if w.baro > w.prevBaro:
            w.p[x-1] = (whiteH)
            w.p[x] = (whiteM)
            w.p[x+1] = (whiteL)
        elif w.baro < w.prevBaro:
            w.p[x+1] = (whiteH)
            w.p[x] = (whiteM)
            w.p[x-1] = (whiteL)
        else:
            w.p[x-1] = w.p[x] = w.p[x+1] = (whiteH)
    w.p.write()
    w.prevBaro = w.baro    

def setTemp(w):
    o = tempOffset
    t = w.temp
    l = w.prevTemp
    #Dim Prev temp
    if w.prevTemp != 200: 
        if l % 2 == 1:
            w.p[math.floor(l/2)+o] = greenL
        w.p[math.ceil(l/2+o)] = greenL
        w.p.write()      
    #Turn on current temp
    if t % 2 == 1:
        w.p[math.floor(t/2)+o] = greenH
    w.p[math.ceil(t/2)+o] = greenH
    w.p.write()
    
    w.prevTemp = w.temp

    
def setWindDir(w): 
    clockwise = True    
    old = w.getWindDir(w.prevWindDir)[1]
    new = w.getWindDir(w.windDir)[1]
    
    if new > old:
        clock = new - old
        counter = old + (23-new)
    elif old > new:
        counter = old - new
        clock = (23-old) +new
    else:
        return
    
    if min(clock, counter) == counter:
        clockwise = False
    
    x = old
    if clockwise:
        while x != new:
            w.p[x] = (clear)
                
            if x == 23:
                x = 0
            else:
                x = x +1
            w.p[x] = (blueH)
            w.p.write()
            time.sleep(.1)                 
    else:        
        while x != new:
            w.p[x] = (clear)
            if x == 0:
                x = 23
            else:
                x = x -1
            w.p[x] = (blueH)
            w.p.write()
            time.sleep(.1)
    
def animateRain(w):
    r = getRainIntensity(w.rainAmt)

    save = list()  
    start = RAIN_OFFSET
    
    for x in reversed(range(start-r[1],start)):
        save.append(w.p.__getitem__(x))
        
    for x in reversed(range(start-r[1], start)):
        
        for c in range(0, 256, 85):
            w.p[x] = ((0, 0, 0+c ))
            w.p.write()
        w.p[x] = (clear)
        w.p.write()
        
    y = 0
    for x in reversed(range(start-r[1],start)):
        w.p[x] = save[y]
        y = y +1
    w.p.write()

def lightning(p, d):
    
    save = list()  
    start = LIGHTNING_OFFSET
    d = 42-(d*2)
    start = start - round(d/2)
    for x in range(d):
        save.append(p.__getitem__(start+x))
        
    
    for y in range(2):
        for x in range(start, start + d):
            p[x] = whiteH
        p.write()
        time.sleep(.05)
    
        for x in range(start, start + d):
            p[x] = clear
        p.write()
        time.sleep(.05)

    y = 0
    for x in range(start, start + d):
        p[x] = save[y]
        y = y +1
    p.write()
    
    return
    
def setRain(w):
    count = w.rainTotal/5
    count = math.ceil(count)
    for x in reversed(range(RAIN_OFFSET - count, RAIN_OFFSET)):
        w.p[x] = blueH
    w.p.write()   

def getRainIntensity(w):
    #rain amount is reported in mm per min, adjust to get per hour.
    i = w * 60
    r = [0,0]
    if i < .25:
        r[0] = "very light"
        r[1] = 3
    elif i < 1:
        r[0] = "light"
        r[1] = 6
    elif i < 4:
        r[0] = "moderate"
        r[1] = 9
    elif i < 16:
        r[0] = "heavy"
        r[1] = 12
    elif i < 50:
        r[0] = "very heavy"
        r[1] = 15
    else:
        r[0] = "extreme"
        r[1] = 18
        
    return r

def setWind(w):
   
    s = windOffset
    n = w.wind + s
    o = w.prevWind + s
    maxGust = w.maxGust + windOffset
    if o == n:
        return

    if o < n:
        #going up
        #Make sure everything below old is on
        for x in range(s, o):
            if w.p.__getitem__(x) !=  (greenH) and w.p.__getitem__(x) !=  (greenL): #Dont touch if this is a temp (green)led
                w.p[x] = (redH)
                w.p.write()
                
        for x in range(o, n):
            if w.p.__getitem__(x)[1] ==  0:
                for c in range(0, 256, 5):
                    w.p[x] = ((0+c, 0, 0 ))
                    w.p.write()      
    else:
        #going down
        
        for x in reversed(range(n, o)):
            if x == maxGust - 1:
                w.p[x] = (fuchsia)               
            else:
                for c in range(0, 256, 5):
                    w.p[x] = ((255-c , 0, 0))
                    w.p.write()

def getMaxGust(w):
    
    preMax = max(w.gustList)
    
    if len(w.gustList) == maxGustMin: 
        w.gustList.pop(0)
    w.gustList.append(w.wind)
    if max(w.gustList) == 0:
        #Turn off previous gust
        w.p[preMax + windOffset-1] = (clear)
          
    elif preMax != max(w.gustList):
        w.p[preMax +  windOffset -1 ] = (clear)
        w.p[max(w.gustList)+ windOffset -1] =(59,2,77)
        
    w.p.write()
    return max(w.gustList)

def checkDate(w):
    global dayNum
    if dayNum != time.localtime(w.epoch-18000)[2] and dayNum != -1:
        w.p.fill(clear)
        w.p.write()
        dayNum = time.localtime(w.epoch-18000)[2]
        w.rainTotal = 0
    



def obs_stHandler(w):   
   
    if w.baro != w.prevBaro:
        setBaro(w)
        w.prevBaro = w.baro
    if w.temp != w.prevTemp:
        setTemp(w)
        w.prevTemp = w.temp
    


def getData(w):
    while True:
        data, addr=s.recvfrom(1024)    
        d = json.loads(data)
        if d['type'] == "rapid_wind":
            w.epoch = d['ob'][0]
            w.wind = round(d['ob'][1] * 2.23694)
            w.windDir = d['ob'][2]          
            w.maxGust = getMaxGust(w)
            setWind(w)
            w.prevWind = w.wind
            setWindDir(w)
            w.prevWindDir = w.windDir
            print("Wind: " + str(w.wind) + " Max Gust: " + str(w.maxGust) + " Dir: " + w.getWindDir(w.windDir)[0])
            checkDate(w)            
            if w.rainAmt > 0:
                animateRain(w)
                
        elif d['type'] == "obs_st":        
            #temp Measurement        
            w.temp = round((d['obs'][0][7]*(9/5) + 32))
            w.rainAmt = d['obs'][0][12]                
            w.rainTotal = w.rainTotal + w.rainAmt
            #Station pressure (add .69 to correct for my altitude)
            w.baro = round((d['obs'][0][6] / 33.8639), 3) + .69          
            print("Temp: " + str(w.temp) + " Baro: " + str(w.baro) + " Rain: " + str(w.rainAmt) + " Rain Total: " + str(w.rainTotal))
            obs_stHandler(w)
            
        elif d['type'] == "evt_strike":
            strikeDist = d['evt'][1]
            lightning(w.p, strikeDist)
    
  
try:
    np = neopixel.NeoPixel(machine.Pin(0), NUM_LED)
    initFlash(np)
    ip = connect(np)    
    addr_info = socket.getaddrinfo(ip, 50222)
    addr = addr_info[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(addr)   
    weather = weatherDevice.WeatherDevice(np)
    getData(weather)
    
    
except KeyboardInterrupt:
    np.fill((0,0,0))
    np.write()