from pathlib import Path
from os import system
from os.path import exists
import re
import csv
import requests
from bs4 import BeautifulSoup

CSV_PATH = "biglist.csv"
#ANKI_MEDIA = ".local/share/Anki2/User 1/collection.media/"
ANKI_MEDIA = "bsl-gcse/testmedia/"


class Note:
    def __init__(self, *args):
        args = args[0]
        self.headword = args[0]
        self.definition = args[1]
        self.example = args[2]
        self.video_url = args[3]
        self.video_title = args[4]
        self.url = args[5]
        self.video_count = args[6]
        self.tags = [normalize_tag(x) for x in args[7]]

    def __str__(self):
        tag_str = " ".join(self.tags)

        joined = ";".join(
            [
                normalize_csv(self.headword),
                normalize_csv(self.definition),
                normalize_csv(self.example),
                f"[sound:{video_filename(self.video_url)}]",
                normalize_csv(self.video_url),
                normalize_csv(self.video_title),
                normalize_csv(self.url),
                normalize_csv(self.video_count),
                normalize_csv(tag_str),
            ]
        )

        return joined


def get_page(url):
    """Get the HTML for a given URL. Parse and return a BeautifulSoup object of it"""
    html = requests.get(url).text
    page = BeautifulSoup(html, "lxml")
    return page


def get_definitions(url, tags):
    """Read h1 and h2 headings for a given URL, and check for presence of video
    For each heading:
        Pull out the 'headword'
        Find tags
        Find definition
        Find example usage
        Find the first video link and details
        Create and append a Note object to the list"""

    page = get_page(url)
    notes = []
    headings = [page.find("h1")] + page.find_all("h2")
    #print(f"URL: {url} found headings h1 {page.find('h1')} and h2 {page.find_all('h2')}")
    if not page.find_all(itemprop="video"):
        print(f"No video available for url: {url}")
        return notes
    video_count = len(page.find_all(itemprop='video'))
    print(f"Findall videoprop = {video_count}")
    for heading in headings:
        headword = heading.text
        tags += [x.text for x in heading.find_next_siblings("span")]
        #print(f"tags: {tags}")
        first_p = heading.find_next_sibling("p")
        #print(f"first_p {first_p}")
        def_string = re.findall("</b> (.*?)<br/>", str(first_p))
        if def_string:
            #print(f"have def_string {def_string}")
            definition = def_string[0]
        else:
            definition = ""
        italics = first_p.find("i")
        if italics is not None:
            example = italics.text
        else:
            example = ""
        video_div = first_p.find_next(itemprop="video")
        #print(f"video_div {video_div}")
        #print(f"video count: {first_p.find_all(itemprop='video')}")
        video_url = video_div.find(itemprop="contentURL")["content"]
        video_title = re.findall("(<i>.*?) <br/>", str(video_div))[0]
        notes.append(
            Note([headword, definition, example, video_url, video_title, url, str(video_count), tags])
        )
    #print("\n\n\n")
    return notes


def normalize_tag(string):
    return string.replace(" ", "_")


def normalize_csv(string):
    doubled_quotes = string.replace('"', '""')
    return f'"{doubled_quotes}"'


def video_filename(url):
    """Replace slashes in video URL with underscores to make a filename"""
    end = re.findall("signbsl.com/(.*)", url)[0]
    return end.replace("/", "_")


def frequency(word):
    """Check 'frequency.txt' for an entry for a word. Return the frequency value
    if present, or 10000 if not"""
    word_file = "frequency.txt"
    reg = re.compile(f"^(\\d+) {word}$", re.MULTILINE)
    with open(word_file, "r") as file:
        filetext = file.read()
    results = reg.findall(filetext)
    if results:
        return int(results[0])
    return 10000


def word_list():
    """Parse the signbsl GCSE vocab list, and generate a word list from it
    Duplicates some function with add_signs. Commonise later"""
    page = get_page("https://www.signbsl.com/gcse-vocabulary")
    notes = []
    for category in page.find_all("h3"):
        pages = [
            "https://signbsl.com" + x["href"]
            for x in category.find_parent().find_all("a")
        ]
        for page in pages:
            print("Contacting ", page, category.text)
            notes += get_definitions(page, [category.text])
    write_csv(CSV_PATH, notes)


def write_csv(filename, notes):
    """Write Notes into a CSV file ordered based on frequency"""
    notes.sort(key=lambda note: frequency(note.headword))
    with open(filename, "w") as file:
        file.writelines([str(note) + "\n" for note in notes])


def convert_video(url):
    """Download and ffmpeg convert videos to save file space in Anki"""
    temp = Path("/tmp/")
    filename = video_filename(url)
    dest = Path.home() / Path(ANKI_MEDIA)
    if exists(dest / filename):
        #print("Already converted", dest / filename)
        return
    response = requests.get(url)
    with open(f"{temp / filename}", mode="wb") as file:
        file.write(response.content)
    command = (
        f'ffmpeg -i "{temp / filename}" -vcodec libx265 -crf 32 "{dest / filename}"'
    )
    system(command)


def download_videos(csv_path):
    """Read notes from CSV, and call through to download/convert the videos"""
    notes = read_csv(csv_path)
    for note in notes:
        convert_video(note.video_url)


def read_csv(path):
    """Read CSV notes, cutting out the fourth item, as the Note object doesn't
    have a self. entry for the anki [sound... string, so while it writes that
    out to CSV, it can't be created from that. Weird limitation that shouldn't
    exist"""
    notes = []
    with open(path) as file:
        reader = csv.reader(file, delimiter=";")
        for row in reader:
            tags = row[8].split(" ")
            # cut out the fourth item (see Note __str__ function)
            row = row[0:3] + row[4:8] + [tags]
            notes.append(Note(row))
    return notes


def add_signs(signs, tags, output):
    """For a list of signs, generate CSV output word list"""
    notes = []
    for sign in signs:
        notes += get_definitions("https://www.signbsl.com/sign/" + sign, tags)
    write_csv(output, notes)

#word_list()
word_list = []
with open('wordlist.txt','r') as f:
    word_list.extend(line.strip('\n') for line in f.readlines())
add_signs(word_list, [], 'testout.csv')
download_videos('testout.csv')
