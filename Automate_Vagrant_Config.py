# Global dictionary declaration, which houses all various configurations for each particular OS Choice
OPERATING_SYSTEMS = {

    "Centos_6.5": {"name": "chef/centos-6.5",
                   "description": "A standard CentOS 6.5 x64 base install",
                   "setting1": "value1",
                   "setting2": "value2",
                   "setting3": "value3",
                   "setting4": "value4"},

    "Ubuntu_12.04_LTS_64bit_Server": {"name": "hashicorp/precise64",
                                      "description": "A standard CentOS 6.5 x64 base install",
                                      "setting1": "value1",
                                      "setting2": "value2",
                                      "setting3": "value3",
                                      "setting4": "value4"},

    "Lucid_32": {"name": "lucid32",
                 "description": "TODO",
                 "setting1": "value1",
                 "setting2": "value2",
                 "setting3": "value3",
                 "setting4": "value4"},
}

# This constant houses the baseline config file
BASE_VAGRANT_CONFIG = """Vagrant.configure("2") do |config|
  config.vm.box ="hashicorp/precise64"
  config.vm.provision :shell, path: "bootstrap.sh"
  config.vm.provider "virtualbox" do |v|
    v.gui = true
  end

end"""

print "Greetings these are the follow choices for operatin systems ",OPERATING_SYSTEMS.keys()," Please select one (case matters)"
#mUserOsChoice is a string which represents the users choice for operating system
#is case sensitive and be aware for underscores
mUserOsChoice=str(input())


# The next line will open the Vagrant configuration as a file object known as f
with open("Vagrantfile", "w+") as f:
    f.write(BASE_VAGRANT_CONFIG)
