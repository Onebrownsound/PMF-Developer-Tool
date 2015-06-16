from bs4 import BeautifulSoup
import requests


class VagrantBox():
    def __init__(self,name,compatability,url,size):
        self.name=str(name)
        self.compatability=compatability
        self.url=url
        self.size=size
    def __repr__(self):
        return str(self.name)


target_url = "http://www.vagrantbox.es/"
target_request = requests.get(target_url)
data = target_request.text
target_soup = BeautifulSoup(data)

parsed_table=[link for link in target_soup.find_all("td")]
VagrantBoxes=[]

while(parsed_table):
    x=VagrantBox(parsed_table.pop(0),parsed_table.pop(0),parsed_table.pop(0),parsed_table.pop(0))
    VagrantBoxes.append(x)

print(VagrantBoxes[0])
