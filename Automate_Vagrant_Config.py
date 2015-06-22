from string import Template
import vagrant
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
    for i, j in enumerate(OPERATING_SYSTEMS.keys(), start=1):
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


def write_vagrant_config(mUserOsChoice):
    print ("...Writing Vagrant Configurations To File...")
    # The next line will open the Vagrant configuration as a file object known as f
    try:
        with open("Vagrantfile", "w+") as f:
            f.write(BASE_VAGRANT_CONFIG.safe_substitute(operating_system=OPERATING_SYSTEMS[mUserOsChoice]["name"]))
    except IOError:
        print("Apparently Vagrantfile does not exist.")
    print("Vagrantfile Succesfully Initialized")


def write_bootstrap_config(data_base_string):
    with open("bootstrap.sh", "w+") as f:
        f.write(BASE_BOOTSTRAP_CONFIG.safe_substitute(rdb=data_base_string))


def query_and_install_boxes(m_system_vagrant_object, m_target_boxes):
    m_vagrant_box_list = []
    for box in m_system_vagrant_object.box_list():
        m_vagrant_box_list.append(box.name)

    print " System Box Status :"
    if not m_vagrant_box_list:
        print("Im sorry no boxes are currently installed. We can fix that! \n")

    for box in m_target_boxes:
        if (box not in m_vagrant_box_list):
            print(box, "is not found! Attempting to connect to server and download")
            try:
                subprocess.call(["vagrant", "box", "add", box, "--provider", "virtualbox"])
            except:
                print "Subprocess error please see logs."
                return
    print "All targeted boxes installed!"


def main():
    # m_target_boxes is a very important list of desired boxes for a particular system
    # the name entered into them must match the name hosted by Vagrant at
    # https://atlas.hashicorp.com/boxes/search
    # if you append to target boxes be sure to manually add an entry into the global dictionary OPERATING_SYSTEMS

    m_target_boxes = ["hashicorp/precise64", "ubuntu/trusty64", "chef/debian-7.4"]

    # Create a Vagrant object for the system in order to retrieve status information and such
    m_system_vagrant_object = vagrant.Vagrant()
    # Query system to see if any boxes are installed
    query_and_install_boxes(m_system_vagrant_object, m_target_boxes)


    # Set m_user_os_choice to null, and repeat prompt until user response matches a key in OPERATING_SYSTEM
    m_user_os_choice = prompt_user_os_choice()
    write_vagrant_config(m_user_os_choice)

    # Create a vagrant box object to fetch the systems box list


if __name__ == "__main__":
    main()
