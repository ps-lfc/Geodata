import sqlite3
import urllib
import time
import ssl
import json
import codecs
import webbrowser

serviceurl = "http://maps.googleapis.com/maps/api/geocode/json?"
scontext = None
conn = sqlite3.connect('geodata.sqlite')
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS Locations (address TEXT, geodata TEXT)''')

fh = open("where.data")
count = 0
for line in fh:
    if count > 200 : break
    address = line.strip()
    print ('')
    cur.execute("SELECT geodata FROM Locations WHERE address= ?", (buffer(address), ))

    try:
        data = cur.fetchone()[0]
        print ("Found in database "),address
        continue
    except:
        pass

    print ('Resolving'), address
    url = serviceurl + urllib.urlencode({"sensor":"false", "address": address})
    print ('Retrieving'), url
    uh = urllib.urlopen(url)
    data = uh.read()
    print ('Retrieved',len(data),'characters',data[:20].replace('\n',' '))
    count = count + 1
    try: 
        js = json.loads(str(data))
        # print js  # We print in case unicode causes an error
    except: 
        continue

    if 'status' not in js or (js['status'] != 'OK' and js['status'] != 'ZERO_RESULTS') : 
        print ('==== Failure To Retrieve ====')
        print (data)
        break

    cur.execute('''INSERT INTO Locations (address, geodata) 
            VALUES ( ?, ? )''', ( buffer(address),buffer(data) ) )
    conn.commit() 
    time.sleep(1)

cur.execute('SELECT * FROM Locations')
fhand = codecs.open('where.js','w', "utf-8")
fhand.write("myData = [\n")
count = 0
for row in cur :
    data = str(row[1])
    try: js = json.loads(str(data))
    except: continue

    if not('status' in js and js['status'] == 'OK') : continue

    lat = js["results"][0]["geometry"]["location"]["lat"]
    lng = js["results"][0]["geometry"]["location"]["lng"]
    if lat == 0 or lng == 0 : continue
    where = js['results'][0]['formatted_address']
    where = where.replace("'","")
    try :
        count = count + 1
        if count > 1 : fhand.write(",\n")
        output = "["+str(lat)+","+str(lng)+", '"+where+"']"
        fhand.write(output)
    except:
        continue

fhand.write("\n];\n")
print count, "records written to where.js"
cur.close()
fhand.close()
webbrowser.open_new_tab('where.html')

