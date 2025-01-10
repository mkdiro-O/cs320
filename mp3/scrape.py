# project: MP3
# submitter: Megan Kuo
# partner: none
# hours: 8

from collections import deque
import os
import pandas as pd
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class GraphSearcher:
    def __init__(self):
        self.visited = set()
        self.order = []

    def visit_and_get_children(self, node):
        """ Record the node value in self.order, and return its children
        param: node
        return: children of the given node
        """
        raise Exception("must be overridden in sub classes -- don't change me here!")

    def dfs_search(self, node):
        self.visited.clear()
        self.order.clear()
        self.dfs_visit(node)
        
    def dfs_visit(self, node):
        if node in self.visited:
            return
        self.visited.add(node)
        children = self.visit_and_get_children(node)
        for child in children:
            self.dfs_visit(child)
            
    def bfs_search(self, node):
        self.visited.clear()
        self.order.clear()
        queue = deque([node]) 
        self.visited.add(node)
        self.bfs_visit(queue)
        
    def bfs_visit(self, queue):
        while queue:
            current_node = queue.popleft()
            children = self.visit_and_get_children(current_node)
            for child in children:
                if child not in self.visited:
                    self.visited.add(child)
                    queue.append(child)
        
        
class MatrixSearcher(GraphSearcher):
    def __init__(self, df):
        super().__init__() # call constructor method of parent class
        self.df = df

    def visit_and_get_children(self, node):
        children = []
        for col, value in self.df.loc[node].items():
            if value == 1:
                children.append(col)
        self.order.append(node) 
        return children


class FileSearcher(GraphSearcher):
    
    def __init__(self):
        super().__init__()

    def visit_and_get_children(self, node):
        file_path = os.path.join("file_nodes", node)
        with open(file_path, "r") as file:
            value = file.readline().strip()
            children = file.readline().strip().split(',')
            self.order.append(value)
            return children

    def concat_order(self):
        return ''.join(self.order)
    
    
class WebSearcher(GraphSearcher):
    
    def __init__(self, driver):
        super().__init__()
        self.driver = driver
        self.tables = []

    def visit_and_get_children(self, node):
        self.order.append(node)
        self.driver.get(node)
        urls = []
        elements = self.driver.find_elements(By.TAG_NAME, "a")
        for element in elements:
            url = element.get_attribute('href')
            if url:
                urls.append(url)
        tables = pd.read_html(self.driver.page_source)
        relevant_table = tables[0]
        self.tables.append(relevant_table)
        return urls

    def table(self):
        return pd.concat(self.tables, ignore_index=True)
    
def reveal_secrets(driver, url, travellog):
    # Generate password from the "clue" column of the travellog DataFrame
    password = ''.join(str(num) for num in travellog['clue'])
    
    # Visit URL with the driver
    driver.get(url)
    
    # Automate typing the password in the box and clicking "GO"
    password_box = driver.find_element(By.ID, 'password-textbox')
    password_box.send_keys(password)
    go_button = driver.find_element(By.ID, 'submit-button')
    go_button.click()
    
    # Wait until the page is loaded
    time.sleep(2)
    
    # Click the "View Location" button
    view_location_button = driver.find_element(By.ID, 'view-location-button')
    view_location_button.click()
    
    # Wait until the result finishes loading
    time.sleep(2)
    
    # Get the URL of the image
    image_url = driver.find_element(By.ID, 'image').get_attribute('src')
    
    
    # Download the image using requests module
    image_response = requests.get(image_url)
    
    # Save the image to a file named 'Current_Location.jpg'
    with open('Current_Location.jpg', 'wb') as img_file:
        img_file.write(image_response.content)
    
    # Return the current location that appears on the page
    current_location = driver.find_element(By.ID, 'location').text
    
    return current_location
  