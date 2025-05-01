from lxml import etree
from collections import Counter

XML_PATH = "data/raw/full_database.xml"   # adjust if your file lives elsewhere

counter = Counter()
# stream through the file; stop after we’ve looked at ~400 elements
for _event, elem in etree.iterparse(XML_PATH, events=("start",)):
    tag_name = elem.tag.split("}")[-1]    # drop namespace if present
    counter[tag_name] += 1
    if sum(counter.values()) >= 400:
        break

print("\nTop tags in the first 400 elements:")
for tag, qty in counter.most_common(20):
    print(f"{tag:<25} {qty}")
