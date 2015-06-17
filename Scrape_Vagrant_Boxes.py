from bs4 import BeautifulSoup
import requests

# Serves as a data structure to house a particular Vagrant Box
class VagrantBox():
    def __init__(self, name, compatability, url, size):
        self.name = name.replace("<td>", "").replace("</td>", "").replace("<br>", "").replace("</br>", "")
        self.itemized_name = [word for word in self.name.split()]
        self.short_name = " ".join(self.itemized_name[0:3])
        self.compatability = compatability.replace("<td>", "").replace("</td>", "").replace("<br>", "").replace("</br>",
                                                                                                                "")
        self.url = url.replace("<td>", "").replace("</td>", "").replace("<br>", "").replace("</br>", "")
        self.size = size.replace("<td>", "").replace("</td>", "").replace("<br>", "").replace("</br>", "")

    def __repr__(self):
        return str(self.short_name)
def main():
    # The following four lines are used to
    # Retrieve the raw HTML from the target_url
    # Convert that html to a Text file
    # Convert that Text into a BeautifulSoup Object
    target_url = "http://www.vagrantbox.es/"
    target_request = requests.get(target_url)
    data = target_request.text
    target_soup = BeautifulSoup(data)

    # The parsed_table houses all the td elements located within the target_url
    parsed_table = [link for link in target_soup.find_all("td")]

    # Initliaze an empty list, which will be used to hold VagrantBox objects
    vagrant_box_container = []

    # Iterates over the parsed_table, while creating a new VagrantBox object for each set of name,compatability,url, and size
    while (parsed_table):
        x = VagrantBox(str(parsed_table.pop(0)), str(parsed_table.pop(0)), str(parsed_table.pop(0)),
                       str(parsed_table.pop(0)))
        vagrant_box_container.append(x)

    # Iterates through VagrantBoxes list and removes those who have a short_name greater than 30Chars
    vagrant_box_container = filter(lambda x: len(x.short_name) < 30, vagrant_box_container)

    # Finally now that we have culled the vagrant_box_container iterate over all housed objects and display their respective
    # short name and url
    for box in vagrant_box_container:
        print(box, box.url)

if __name__ == "__main__":
    main()
