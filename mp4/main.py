import pandas as pd
from flask import Flask, request, jsonify
import time
from zipfile import ZipFile
import re
from collections import Counter
import geopandas as gpd
import json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt 
from shapely.geometry import Point, Polygon, box

app = Flask(__name__)
last_request_time = {}

homepage_visits = 0

clicks_A = 0
clicks_B = 0

@app.route("/")
def home():
    global homepage_visits, clicks_A, clicks_B
    homepage_visits += 1
    
    with open("index.html") as f:
        html = f.read()
        
    if homepage_visits <= 10:
        version = 'A' if homepage_visits%2 == 0 else 'B'
    else:
        version = 'A' if clicks_A >= clicks_B else 'B'
        
    donate_link_html = '<a href="donate.html?from={}" style="color: {};">Donate</a>'
    
    if version == 'A':
        donate_link_color = 'blue'
    else:
        donate_link_color = 'red'
        
    html = html.replace('<!-- DONATE_LINK_PLACEHOLDER -->', donate_link_html.format(version, donate_link_color))
    
    print(html)
    
    return html

@app.route('/browse.html')
def browser_handler():
    df = pd.read_csv('server_log.zip', compression='zip', nrows=500)
    html_table = df.to_html()
    html = "<html><head></head><body><h1>Browse first 500 rows of rows.csv</h1>{}</body></html>".format(html_table)

    return html

@app.route('/browse.json')
def browse_json():
    client_ip = request.remote_addr
    
    if client_ip in last_request_time:
        if time.time() - last_request_time[client_ip] < 60:
            # Calculate the time until the next allowed request
            retry_after = int(60 - (time.time() - last_request_time[client_ip]))
            # Include the "Retry-After" header in the response
            headers = {'Retry-After': retry_after}
            return jsonify({'error': 'Too many requests. Please try again later.'}), 429, headers
    
    last_request_time[client_ip] = time.time()
    
    df = pd.read_csv('server_log.zip', compression='zip')
    data = df.to_dict(orient='records')
    
    return jsonify(data)

@app.route('/visitors.json')
def visitors_json():
    return jsonify(list(last_request_time.keys()))

@app.route('/donate.html')
def donate():
    global clicks_A, clicks_B
    html = ""
    source = request.args.get('from')
    
    if source == 'A':
        clicks_A += 1
        html = "PLEASE DONATE"
    elif source == 'B':
        clicks_B += 1
        html = "PLEASE DONATE PLEASE"
        
    return html


class Filing:
    def __init__(self, html):
        self.dates = self.extract_dates(html)
        self.sic = self.extract_sic(html)
        self.addresses = self.extract_addresses(html)

    def state(self):
        for address in self.addresses:
            match = re.search(r'\b[A-Z]{2}\s\d{5}\b', address)
            if match:
                return match.group()[:2]
        return None

    def extract_dates(self, html):
        dates = re.findall(r'\b(19|20)\d{2}-\d{2}-\d{2}\b', html)
        return [date for date in dates if 1900 <= int(date[:4]) <= 2099]

    def extract_sic(self, html):
        match = re.search(r'SIC=(\d+)', html)
        return int(match.group(1)) if match else None

    def extract_addresses(self, html):
        addresses = []
        for addr_html in re.findall(r'<div class="mailer">(.*?)</div>', html, re.DOTALL):
            lines = []
            for line in re.findall(r'<span class="mailerAddress">(.*?)</span>', addr_html, re.DOTALL):
                stripped_line = line.strip()
                if stripped_line:  # Check if the stripped line is not empty
                    lines.append(stripped_line)
            if lines:  # Check if there are any non-empty lines
                addresses.append("\n".join(lines))
        return addresses
    
def get_sic_from_filing(zip_file_name, file_name):
    with ZipFile(zip_file_name,'r') as z:
        with z.open(filename) as f:
            html_content = f.read().decode('utf-8')
            filing = Filing(html_content)
            return filing.sic
            
def count_addresses_in_filings():
    filings = {}
    with ZipFile("docs.zip") as zf:
        for info in zf.filelist:
            if info.filename.split(".")[-1] in ("htm","html"):
                with zf.open(info.filename) as f:
                    filings[info.filename] = Filing(str(f.read(), "utf-8"))
    with ZipFile('server_log.zip', 'r') as server_zip:
        with server_zip.open('rows.csv') as log_file:
            data = pd.read_csv(log_file)
    addresses =[]
    for row in data.itertuples():
        path = f"{int(row.cik)}/{row.accession}/{row.extention}" 
        if path in filings:
            addresses.extend(filings[path].addresses)
    counts = pd.Series(addresses).value_counts()
    return counts[counts >= 300].to_dict()

@app.route("/analysis.html")
def analysis():
    df_logs = pd.read_csv('server_log.zip', compression = 'zip')
    top_ips = df_logs.groupby('ip').size().sort_values(ascending = False).head(10).to_dict()
    top_ips_str = ', '.join([f"'{ip}': {count}" for ip, count in top_ips.items()])
    
    sic_codes = []
    with ZipFile('docs.zip', 'r') as z:
        for filename in z.namelist():
            if filename.endswith('.htm') or filename.endswith('.html'):
                with z.open(filename) as f:
                    html_content = f.read().decode('utf-8')
                    filing = Filing(html_content)
                    if filing.sic is not None:
                        sic_codes.append(filing.sic)
                        
    sic_code_distribution = pd.Series(sic_codes).value_counts().head(10).to_dict()
    sic_code_distribution_str = "<br>".join([f"{sic}: {count}" for sic, count in sic_code_distribution.items()])
    
    common_addresses = count_addresses_in_filings()

    dashboard_svg = generate_dashboard()
    
    html_content = f"""
    <html>
    <head>
        <title>Analysis of EDGAR Web Logs</title>
    </head>
    <body>
        <h1>Analysis of EDGAR Web Logs</h1>
        <p>Q1: how many filings have been accessed by the top ten IPs?</p>
        <p>{{{top_ips_str}}}</p>
        <p>Q2: what is the distribution of SIC codes for the filings in docs.zip?</p>
        <p>{{{sic_code_distribution_str}}}</p>
        <p>Q3: what are the most commonly seen street addresses?</p>
        <p>{common_addresses}</p>
        <p><b>Dashboard: geographic plotting of postal code</b><p>
        <p>{dashboard_svg}</p>
    </body>
    </html>
    """
    return html_content.replace('<br>', ', ')


def generate_dashboard():
    
    matplotlib.use('Agg')
    points_gdf = gpd.read_file('locations.geojson')
    points_gdf['postal_code'] = points_gdf[ 'address'].str.extract(r'(\d{5})')
    points_gdf.dropna(subset=['postal_code'], inplace=True)
    points_gdf['postal_code'] = points_gdf['postal_code'].astype(int)
    points_gdf = points_gdf[(points_gdf['postal_code'] >= 25000) & (points_gdf['postal_code'] <= 65080)]
    gdf = gpd.GeoDataFrame(points_gdf, geometry =gpd.points_from_xy(points_gdf. geometry.x, points_gdf.geometry.y))
    window = box(-95, 25, -60, 50)
    df2 = gpd.read_file('shapes/cb_2018_us_state_20m.shp')
    fig, ax = plt.subplots()
    df2.intersection(window).to_crs(epsg=2022).plot(ax=ax, color="lightgray")
    gdf[~gdf.intersection(window).is_empty].to_crs(epsg=2022).plot(ax=ax, column='postal_code', cmap='RdBu', legend=True)
    plt.savefig('dashboard.svg')
    plt.close(fig)
              
    with open( 'dashboard.svg','r') as f:
        svg_content = f.read()
              
    return svg_content


    
if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, threaded=False) # don't change this line!

# NOTE: app.run never returns (it runs for ever, unless you kill the process)
# Thus, don't define any functions after the app.run call, because it will
# never get that far.
