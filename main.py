import requests
import re


import time
import csv
import json
import random
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "Connection": "keep-alive",
    "Referer": "https://www.suchajun.com/richang/xingzhengquhuadaima?q=",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
    "sec-ch-ua": "\"Microsoft Edge\";v=\"143\", \"Chromium\";v=\"143\", \"Not A(Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\""
}
cookies = {
    "scjuid": "dqc5vpl99gq4s8ko8rbbqfog4k",
    "_csrf": "d7f8fe71429999f110e724cce45daaacf8c8192702c42a3425ff4de1a6704574a%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%22JAto3-BzNnqqna-wwKcAd40HIQAbRSgF%22%3B%7D"
}
url = "https://www.suchajun.com/richang/xingzhengquhuadaima"
params = {
    "q": ""
}
requests.packages.urllib3.disable_warnings()
base_url = "https://www.suchajun.com"

# Setup Session with retries
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount('http://', adapter)
session.mount('https://', adapter)
session.headers.update(headers)
session.cookies.update(cookies)

def get_data(url):
    try:
        # Random delay before request to behave more like a human
        time.sleep(random.uniform(3.0, 6.0))
        response = session.get(url, verify=False, timeout=20)
        response.encoding = 'utf-8'
        
        # Check if redirected to verification page
        if 'verify' in response.url or '39.97.5.232' in response.url:
             print(f"Warning: Redirected to verification page for {url}")
             return ""

        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        # If error occurs (like the SSL verification redirect), wait longer and return empty
        time.sleep(10)
        return ""

print("Fetching Level 1...")
response_text = get_data(url)

# Extract data
pattern_level1 = r'<td><a href="([^"]+)">([^<]+)</a></td>\s*<td>(\d+)</td>'

# Pattern for direct links (like Beijing -> Dongcheng)
pattern_level2_link = r'<div class="col"><a[^>]+href="([^"]+)"[^>]*>([^<]+)</a></div>\s*<div class="col">(\d+)</div>'

# Pattern for JS expandable links (like Hebei -> Shijiazhuang)
# <div class="col"><span>+</span><a href="javascript:void(0);" class="city" data-code="130100">石家庄市</a></div>
pattern_level2_js = r'<div class="col">.*<a href="javascript:void\(0\);" class="city" data-code="(\d+)">([^<]+)</a></div>'

# Pattern for Level 3 inside the expandable div (Shijiazhuang -> Changan)
# <div class="col">&nbsp;&nbsp;<a href="/richang/xingzhengquhuadaima/130102">长安区</a></div>
pattern_level3 = r'<div class="col">&nbsp;&nbsp;<a href="([^"]+)">([^<]+)</a></div>\s*<div class="col">(\d+)</div>'

matches = re.findall(pattern_level1, response_text)

results = []

print("行政区划名称|行政区划代码|二级链接")

# target_provinces = ["辽宁省", "福建省", "广西壮族自治区", "海南省", "甘肃省", "青海省"]
target_provinces = [] # Process all

for link, name, code in matches:
    if target_provinces and name not in target_provinces:
        continue

    link = link.strip().rstrip(':') # Fix: Remove trailing colon and whitespace
    full_link = base_url + link
    print(f"{name}|{code}|{full_link}")
    
    level1_data = {
        "name": name,
        "code": code,
        "link": full_link,
        "level": 1,
        "children": []
    }
    results.append(level1_data)
    
    # Fetch Level 2
    time.sleep(0.5) # Add delay to avoid being blocked
    level2_text = get_data(full_link)
    
    # Try finding standard links first (like Beijing)
    matches_level2 = re.findall(pattern_level2_link, level2_text)
    
    if matches_level2:
        for l2_link, l2_name, l2_code in matches_level2:
            if l2_code == code:
                continue # Skip self
            l2_full_link = base_url + l2_link
            print(f"\t{l2_name}|{l2_code}|{l2_full_link}")
            
            level2_data = {
                "name": l2_name,
                "code": l2_code,
                "link": l2_full_link,
                "level": 2,
                "parent_code": code,
                "children": []
            }
            level1_data["children"].append(level2_data)
            
    # Try finding JS expandable links (like Hebei)
    matches_level2_js = re.findall(pattern_level2_js, level2_text)
    if matches_level2_js:
        for l2_code, l2_name in matches_level2_js:
             l2_full_link = f"{base_url}/richang/xingzhengquhuadaima/{l2_code}"
             print(f"\t{l2_name}|{l2_code}|{l2_full_link}")
             
             level2_data = {
                "name": l2_name,
                "code": l2_code,
                "link": l2_full_link,
                "level": 2,
                "parent_code": code,
                "children": []
             }
             level1_data["children"].append(level2_data)

             # Extract children (Level 3) for this city
             # We look for the div with id="county-{code}"
             # Since we don't have a robust HTML parser, we'll try to capture the content until the next div class="row" that is NOT part of this block, 
             # OR just look for pattern_level3 inside the specific chunk.
             
             # Better way: split the text by 'id="county-'
             # But let's try a regex that matches the div content.
             # <div id="county-130100" class="county m-3 mt-0 mb-0"> ... content ... </div>
             # The content contains multiple <div class="row ..."> ... </div>
             
             # Let's find the start index
             start_marker = f'id="county-{l2_code}"'
             start_pos = level2_text.find(start_marker)
             if start_pos != -1:
                 # Find the end of this div. It's risky without counting braces.
                 # However, the structure seems consistent.
                 # Let's just search for pattern_level3 starting from start_pos
                 # until we hit something that looks like the start of another city or end of container.
                 
                 # Let's limit the search range to, say, 10000 chars or until next 'id="county-'
                 remaining_text = level2_text[start_pos:]
                 next_marker_pos = remaining_text.find('id="county-', 1) # Find next county block
                 if next_marker_pos != -1:
                     block_text = remaining_text[:next_marker_pos]
                 else:
                     block_text = remaining_text
                 
                 matches_l3 = re.findall(pattern_level3, block_text)
                 for l3_link, l3_name, l3_code in matches_l3:
                     l3_full_link = base_url + l3_link
                     print(f"\t\t{l3_name}|{l3_code}|{l3_full_link}")
                     
                     level3_data = {
                        "name": l3_name,
                        "code": l3_code,
                        "link": l3_full_link,
                        "level": 3,
                        "parent_code": l2_code
                     }
                     level2_data["children"].append(level3_data)

# Save to JSON
with open('administrative_divisions.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)
print("Saved to administrative_divisions.json")

# Save to CSV
with open('administrative_divisions.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Level', 'Name', 'Code', 'Link', 'Parent Code'])
    
    def write_node(node, parent_code=""):
        writer.writerow([node['level'], node['name'], node['code'], node['link'], parent_code])
        if 'children' in node:
            for child in node['children']:
                write_node(child, node['code'])
                
    for item in results:
        write_node(item)

print("Saved to administrative_divisions.csv")




