from string import Template
import subprocess

# Global dictionary declaration, which houses all various configurations for each particular OS Choice
OPERATING_SYSTEMS = {
    "hashicorp/precise64": {"name": "hashicorp/precise64",
                            "description": " A standard Ubuntu 12.04 LTS 64-bit box.",
                            },

    "ubuntu/trusty64": {"name": "ubuntu/trusty64",
                        "description": "Official Ubuntu Server 14.04 LTS (Trusty Tahr) builds",
                        },
    "chef/debian-7.4": {"name": "chef/debian-7.4",
                        "description": "A standard Debian 7.4 x64 base install",
                        },
    "chef/ubuntu-14.04": {"name": "chef/ubuntu-14.04",
                          "description": "A standard chef/ubuntu-14.04 x64 base install",
                          }

}
# This constant houses the baseline config file AS A TEMPLATE OBJECT
# Template objects may not be treated as regular strings
# In order to extract strings from a template object use the TEMPLATEOBJECT.safe_substitute() method,
# Which will return the template object as a string with the appropriate substitutions
BASE_VAGRANT_CONFIG = Template("""Vagrant.configure("2") do |config|
  config.vm.box = "${operating_system}"
  config.vm.provision :shell, path: "bootstrap.sh"
  config.vm.network "public_network", use_dhcp_assigned_default_route:true
   config.vm.provider :virtualbox do |vb|
     vb.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
     vb.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
     vb.customize ["modifyvm", :id, "--memory", "2048"]
   end
end""")


# function responsible for prompting user for OS Choice
def prompt_user_os_choice():
    m_choice_list = {}
    for i, j in enumerate(OPERATING_SYSTEMS, start=1):
        m_choice_list[i] = j

    print "\nPlease select one (case matters):\n"
    for index, option in m_choice_list.items():
        print index, option, OPERATING_SYSTEMS[option]["description"]

    m_user_input = None

    while (m_user_input is None or m_user_input not in m_choice_list.keys()):
        m_user_input = int(raw_input())
        if (m_user_input not in m_choice_list.keys()):
            print("Sorry that is not an acceptable input please try again or exit the program.")


    # mUserOsChoice is a string which represents the users choice for operating system
    # is case sensitive and be aware for underscores
    return m_choice_list[m_user_input]


# Opens the Vagrantfile in the directory and writes the specifief options to the file and saves it
def write_vagrant_config(mUserOsChoice):
    print ("...Writing Vagrant Configurations To File...")
    # The next line will open the Vagrant configuration as a file object known as f
    try:
        with open("Vagrantfile", "w+") as f:
            f.write(BASE_VAGRANT_CONFIG.safe_substitute(operating_system=OPERATING_SYSTEMS[mUserOsChoice]["name"]))
    except IOError:
        print("Apparently Vagrantfile does not exist.")
    print("Vagrantfile Succesfully Initialized")


# Function currently does not get called, but could be useful in the future.
def write_bootstrap_config(data_base_string):
    with open("bootstrap.sh", "w+") as f:
        f.write(BASE_BOOTSTRAP_CONFIG.safe_substitute(rdb=data_base_string))


def query_and_install_boxes(m_currently_installed_boxes):
    # Use the vagrant system object to list out all currently installed boxes and append them to m_currently_installed_boxes
    print " System Box Status :"

    # Will trigger only if no boxes are installed
    if not m_currently_installed_boxes:
        print("Im sorry no boxes are currently installed. We can fix that! \n")

    # Iterate through desired boxes and check if they are in installed boxes. If they are desired and not installed go download them from vagrants server.
    for box in OPERATING_SYSTEMS:
        if (box not in m_currently_installed_boxes):
            print(box, "is not found! Attempting to connect to server and download")
            try:
                subprocess.call(["vagrant", "box", "add", box, "--provider", "virtualbox"])
            except:
                print "Subprocess error please see logs."
                return
    print "All targeted boxes installed!"


def fetch_system_boxes():
    m_box_results = []
    # Automates calling "vagrant box list" from the cmd line
    m_query_system = subprocess.check_output(["vagrant", "box", "list"]).split("\n")
    for item in m_query_system:
        # Does string manipulation to essentially extract only the most important parts of the "vagrant box list" cmd
        try:
            box_name = item.rstrip().split()
            m_box_results.append(box_name[0])
        except:
            pass
    return m_box_results


def main():
    # Create a Vagrant object for the system in order to retrieve status information and such
    # Query system to see if any boxes are installed
    m_installed_vagrant_boxes = fetch_system_boxes()

    query_and_install_boxes(m_installed_vagrant_boxes)

    m_user_os_choice = prompt_user_os_choice()
    write_vagrant_config(m_user_os_choice)


if __name__ == "__main__":
    main()
