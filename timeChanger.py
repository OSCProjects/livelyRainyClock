import subprocess as cmd
import time as t
import datetime as d
import requests as r
import json

jsonFile = open('settings.json')
jsonData = json.load(jsonFile)

MinBright = jsonData["brightness"]["Minimum Brightness"]
MaxBright = jsonData["brightness"]["Maximum Brightness"]

MinTime = 0
MaxTime = 86399

l = jsonData["Livelycu.exe path"]
WALLPAPERproperty = jsonData["Brightness property"]

lat = jsonData["Location"]["Latitude"]
lng = jsonData["Location"]["Longitude"]

Told = False

def getResponse(url):
    try:
        response = r.get(url)
        print(response)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error occurred while requesting data from {url}: {e}")
        return None

def SunCalculate(lat, lng):
    data = getResponse(f"https://api.sunrisesunset.io/json?lat={lat}&lng={lng}")
    print(data)
    
    if data:
        dawn = data["results"]["dawn"]
        dusk = data["results"]["dusk"]
        
        DwnPM = False
        DskPM = False

        if "AM" in dawn:
            dawn = dawn.replace("AM", '')
        elif "PM" in dusk:
            print("WARMING: dawn is at PM time, check if dawn is not dusk")
            dawn = dawn.replace("PM", '')
            DwnPM = True
        else:
            print("ERROR: dawn is not in PM nor AM, make sure the correct API is being used")
            return None
        if "PM" in dusk:
            dusk = dusk.replace("PM", '')
            DskPM = True
        elif "AM" in dusk:
            print("WARMING: dusk is at AM time, check if dusk is not dawn")
            dusk = dusk.replace("AM", '')
        else:
            print("ERROR: dusk is not in PM nor AM, make sure the correct API is being used")
            return None
        
        srH, srM, srS = dawn.split(":")
        ssH, ssM, ssS = dusk.split(":")
        
        UssH = int(ssH) * 3600
        UssM = int(ssM) * 60
        UsrH = int(srH) * 3600
        UsrM = int(srM) * 60
        
        Udawn = UsrH + UsrM + int(srS)
        Udusk = UssH + UssM + int(ssS)
        
        if DwnPM == True:
            Udawn += 43200
        if DskPM == True:
            Udusk += 43200
        
        return Udawn, Udusk
    else: 
        print("ERROR: No data returned")
        return None

def setBrightness(brightness):
    try:
        cmd.run([l, "setprop", "--property", f"{WALLPAPERproperty}={brightness}"])
        return brightness
    except Exception as e:
        print(f"Error setting brightness: {e}")
        return None

def lineBreak(spaces):
    for i in range(spaces):
        print("")

def startInformation(middle, dawn, dusk, onePart):
    global Told
    
    if Told == True:
        return False
    
    lineBreak(2)
    
    print(f"Middle = {middle}")
    print(f"dawn = {dawn}")
    print(f"dusk = {dusk}")
    print(f"onePart = {onePart}")
    
    lineBreak(3)
    
    Told = True
    return True

def UseTime():
    
    before = d.datetime.now()
    past = {
        "hours": before.hour,
        "minutes": before.minute,
        "seconds": before.second,
        "unixpast": before.hour * 3600 + before.minute * 60 + before.second,
    }
    
    dawn, dusk = SunCalculate(lat, lng)
    
    if dawn is None or dusk is None:
        print("Unable to calculate dawn and dusk times.")
        return
    
    currentBright = setBrightness(MinBright)
    
    t.sleep(1)
    
    while True:
        
        now = d.datetime.now()
        
        current = { 
            "hours": now.hour,
            "minutes": now.minute,
            "seconds": now.second,
            "unixnow": now.hour * 3600 + now.minute * 60 + now.second,
        }
        
        if current["unixnow"] == 0:
            print("New day detected, checking for new Dawn and Dusk time")
            dawn, dusk = SunCalculate(lat, lng)
            if dawn is None or dusk is None:
                print("Unable to calculate dawn and dusk times.")
                return
            else:
                print(f"New dawn and dusk found! | {dawn} | -- | {dusk} |")
        
        useUnix = current["unixnow"]
        useDusk = dusk
        
        middle = MaxTime / 2
        
        onePart = middle / (MaxBright - MinBright)
        
        updateBrightness = MinBright + int(useUnix / onePart)
        
        startInformation(middle, dawn, dusk, onePart)
        
        if current != past:
            past = current
            
            if useUnix <= middle:
                
                if useUnix >= MinTime and useUnix <= dawn:
                    
                    currentBright = setBrightness(MinBright)
                    
                elif useUnix != MinTime and useUnix > dawn and useUnix < middle:
                    
                    updateBrightness = int(useUnix - dawn) / onePart
                    currentBright = setBrightness(updateBrightness)
                    
                elif useUnix == middle:
                    
                    currentBright = setBrightness(MaxBright)
                    
            if useUnix > middle:
                
                if useUnix == useDusk:
                    
                    currentBright = setBrightness(MinBright)
                    
                elif useUnix != useDusk and useUnix < useDusk:
                    
                    updateBrightness = MaxBright - int(int(useUnix - middle) / onePart)
                    currentBright = setBrightness(updateBrightness)
                    
                    
            print(f"\r{current["hours"]} : {current["minutes"]} : {current["seconds"]}\nCurrent unix = {current['unixnow']}\nCurrent brightness {currentBright:.4f}", end="")
            print("\033[F\033[F", end="")
        
        else:
            pass

UseTime()