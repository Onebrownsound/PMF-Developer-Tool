from string import Template

# Global dictionary declaration, which houses all various configurations for each particular OS Choice
OPERATING_SYSTEMS = {
    "Ubuntu 12.04 LTS 64bit Server": {"name": "hashicorp/precise64",
                                      "description": " A standard Ubuntu 12.04 LTS 64-bit box.",
                                      },

    "Lucid 32": {"name": "lucid32",
                 "description": "TODO",
                 },
    "Ubuntu Server 14.04 LTS": {"name": "ubuntu/trusty64",
                                "description": "Official Ubuntu Server 14.04 LTS (Trusty Tahr) builds",
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

BASE_BOOTSTRAP_CONFIG = Template("""#!/usr/bin/env bash

sudo apt-get update
for i in python3; do
  sudo apt-get install $i -y
${rdb}
done""")

DATABASE={
1: """sudo debconf-set-selections <<< 'mysql-server mysql-server/root_password password'
sudo debconf-set-selections <<< 'mysql-server mysql-server/root_password_again password'
sudo apt-get -y install mysql-client mysql-server""",

2:"sudo apt-get -y install postgresql"}


# function responsible for prompting user for OS Choice
def PromptUserOSChoice():
    choice_list = {}
    for i, j in enumerate(OPERATING_SYSTEMS.keys(), start=1):
        choice_list[i] = j

    print "\nGreetings these are the follow choices for operating systems Please select one (case matters):\n"
    for key, value in choice_list.items():
        print(key, value)

    user_input = None
    while (user_input is None or user_input not in choice_list.keys()):
        user_input = int(raw_input())
        if (user_input not in choice_list.keys()):
            print("Sorry that is not an acceptable input please try again or exit the program.")


    # mUserOsChoice is a string which represents the users choice for operating system
    # is case sensitive and be aware for underscores
    return choice_list[user_input]


def WriteVagrantConfig(mUserOsChoice):
    print ("...Writing Vagrant Configurations To File...")
    # The next line will open the Vagrant configuration as a file object known as f
    try:
        with open("Vagrantfile", "w+") as f:
            f.write(BASE_VAGRANT_CONFIG.safe_substitute(operating_system=OPERATING_SYSTEMS[mUserOsChoice]["name"]))
    except IOError:
        print("Apparently Vagrantfile does not exist.")
    print("Vagrantfile Succesfully Initialized")

def PromptUserDBChoice():
    print("Please select from the following options for databases. \n1. MYSQL\n2. POSTGRESQL\n")
    user_input=int(raw_input())
    while (user_input not in range(1,4)):
        print("Sorry that is not an acceptable input please try again or exit the program.")
        user_input=int(raw_input())
    return user_input

def WriteBootstrapConfig(data_base_string):
    with open("bootstrap.sh","w+") as f:
        f.write(BASE_BOOTSTRAP_CONFIG.safe_substitute(rdb=data_base_string))



def main():
    # Set mUserOsChoice to null, and repeat prompt until user response matches a key in OPERATING_SYSTEM
    mUserOsChoice = PromptUserOSChoice()
    WriteVagrantConfig(mUserOsChoice)
    #mUserDBChoice =PromptUserDBChoice()
    #WriteBootstrapConfig(DATABASE[mUserDBChoice])

if __name__ == "__main__":
    main()
