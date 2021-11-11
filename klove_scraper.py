from urllib.request import urlopen
from collections import namedtuple
import csv
import datetime

ntSong = namedtuple("ntSong", "song_id artist song_name last_played minutes_ago approx_playtime")
csv_file_name = "/home/pi/Python/klove/klove.csv"
recently_played_list = list([])

def load_last_n_played_songs(p_numrows):
    file = open(csv_file_name)
    csv_reader = csv.reader(file)
    lines = len(list(csv_reader))
    start_ndx = lines - p_numrows + 1
    
    with open(csv_file_name) as csv_file_lp:
        csv_reader = csv.reader(csv_file_lp, delimiter=',')
        line_count = 0
        for row in csv_reader:
            line_count = line_count + 1
            if line_count >= start_ndx:
                #print(row)
                recently_played_list.append(row)
    
    return len(recently_played_list)

def remove_html_special_chars(p_str):
    rtrn = p_str.replace("&#39;", "'")
    rtrn = rtrn.replace("&amp;", "&")
    return rtrn

def song_played_recently(p_songid):
    rtrn = 0
    
    for x in range(len(recently_played_list)):
        rp = recently_played_list[x]
        if rp[1] == p_songid:
            # print("Song found: ", p_songid)
            rtrn = rtrn + 1
            
    if rtrn == 0:
        print("Song not found: ", p_songid)
    
    return rtrn

def scrape_klove():

    url = "https://www.klove.com/music/songs"
    dt = datetime.datetime.now()
    print("KLOVE scrape started at: ", dt.strftime("%Y-%m-%d %H:%M"))

    page = urlopen(url)

    html_bytes = page.read()
    html = html_bytes.decode("utf-8")

    end_ndx = 0
    song_ndx = 0
    
    while html.find("<div class=\"card diffuse border-0 h-100 song-card\" id=\"", end_ndx+1) > 0:
        # Find the Song ID
        start_ndx = html.find("<div class=\"card diffuse border-0 h-100 song-card\" id=\"", end_ndx+1) + len("<div class=\"card diffuse border-0 h-100 song-card\" id=\"")
        end_ndx = html.find("\"", start_ndx +1)
        song_id = html[start_ndx:end_ndx]

        # Find the Last Played Tag
        start_ndx = html.find("<p class=\"text-center small text-uppercase mb-2 text-primary\">", end_ndx+1) + len("<p class=\"text-center small text-uppercase mb-2 text-primary\">")
        end_ndx = html.find("</p>", start_ndx +1)
        last_played = html[start_ndx:end_ndx]
        if last_played == "Last Played":
            last_played = "Now Playing"
            minutes_ago = 0
        else:
            minutes_ago = int(last_played[0:last_played.find(" ")])
        
        approx_playtime = dt - datetime.timedelta(minutes = minutes_ago)

        # Find the Song Name
        start_ndx = html.find("<h5 class=\"text-center font-weight-bold\">", end_ndx+1) + len("<h5 class=\"text-center font-weight-bold\">")
        end_ndx = html.find("</h5>", start_ndx +1)
        song_name = remove_html_special_chars(html[start_ndx:end_ndx])

        #Find the Artist
        start_ndx = html.find("<p class=\"text-center card-author small mb-0\">By <span class=\"font-weight-bold\">", end_ndx+1) + len("<p class=\"text-center card-author small mb-0\">By <span class=\"font-weight-bold\">")
        end_ndx = html.find("</span></p>", start_ndx +1)
        artist = remove_html_special_chars(html[start_ndx:end_ndx])
        
        song = ntSong(song_id, artist, song_name, last_played, minutes_ago, approx_playtime)
        
        # ACF - 2021-11-11 - Changed this IF block to skip the "Last Played" song.  This will get more accurate approx_playtime timestamps.
        if minutes_ago == 0:
            #Skip the Now Playing song to get more accurate timestamps
            song_ndx = 0
            print("Skipping currently playing: ", song_id)
        elif song_ndx == 0:
            songlist = [song]
            song_ndx = song_ndx + 1
        else:
            songlist.append(song)
            song_ndx = song_ndx + 1
    return songlist


#Main program goes here....

#Step 1 - Read the CSV file and get the last 10 songs
s_count = load_last_n_played_songs(10)

#Step 2 - Scrape the KLOVE website - grab the songs played list
song_list = scrape_klove()
song_list.reverse()

#Step 3 - Loop through the song list - write songs not in recently played to the CSV
# write_csv(song_list, csv_file_name)

rows_written = 0

for i in range(len(song_list)):
    s = song_list[i]
    #print(i, s.approx_playtime, s.song_id, s.artist, "-", s.song_name)
    row_contents = [s.approx_playtime.strftime("%Y-%m-%d %H:%M"), s.song_id, s.artist, s.song_name]
    
    if song_played_recently(s.song_id) == 0:
    # Open file in append mode
        with open(csv_file_name, 'a+', newline='') as csv_file:
            # Create a writer object from csv module
            csv_writer = csv.writer(csv_file, dialect='unix', quoting=csv.QUOTE_ALL)
            # Add contents of list as last row in the csv file
            csv_writer.writerow(row_contents)
        
            rows_written = rows_written + 1
    
print ("CSV rows written: ", rows_written)
