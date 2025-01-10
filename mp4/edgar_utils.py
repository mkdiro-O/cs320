import pandas as pd
from bisect import bisect
import re

ips = pd.read_csv("ip2location.csv")

def lookup_region(ip):
    ip_numeric = ''.join(c if c.isdigit() else '0' if c != '.' else '.' for c in ip)
    ip_to_int = lambda ip: sum(int(num) * (256 ** index) for index, num in enumerate(ip.split('.')[::-1]))
    vm_ip_int = ip_to_int(ip_numeric)
    
    idx = bisect(ips['high'], vm_ip_int)
    return ips.iloc[idx].region

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
