from string import Template
import subprocess, os, argparse

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

REPORTING_SERVER_OPTIONS = {
    1: "80",
    2: "81",
    3: "82",
    4: "HEAD"
}

MAJ_CLIENT_OPTIONS = {
    1: "80",
    2: "81",
    3: "82"
}

MIN_CLIENT_OPTIONS = {
    "80": {1: "08", 2: "09", 3: "10"},
    "81": {1: "05"},
    "82": {1: "00"}
}
# DYNAMIC_CLIENT_OPTIONS is a on the fly global dictionary built up by scanning bigport for valid client versions
DYNAMIC_CLIENT_OPTIONS = {}

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

BASE_SHELL_SCRIPT = Template("""#!/usr/bin/env bash

#Setup the start time
STARTTIME=$(date +%s)

#Preset the MySQL root password for use later
sudo debconf-set-selections <<< 'mysql-server-5.5 mysql-server/root_password password root'
sudo debconf-set-selections <<< 'mysql-server-5.5 mysql-server/root_password_again password root'

#Update the packages and install the required ones
apt-get update
apt-get install -y tomcat7 tomcat7-admin vim mysql-server-5.5 apache2 libapache2-mod-jk openjdk-6-jre openjdk-6-jdk libc6 ksh rpm subversion libmysql-java

#Update Tomcat & Apache for using port 80
sed -i 's/<Connector port="8080"/<Connector port="8009" protocol="AJP\/1.3" redirectPort="8443" \/>\\n<Connector port="8080"/' /etc/tomcat7/server.xml
sed -i 's/\/etc\/libapache2-mod-jk\/workers.properties/\/etc\/apache2\/workers.properties/' /etc/apache2/mods-available/jk.conf
cp /vagrant/workers.properties /etc/apache2/workers.properties
cp /vagrant/000-default /etc/apache2/sites-available/default
cp /vagrant/000-default /etc/apache2/sites-available/000-default.conf
/etc/init.d/tomcat7 stop
/etc/init.d/apache2 stop


#Setup java permissions for ReportCaster and Derby to listen on ports 8200 & 1527
echo 'grant {    permission java.net.SocketPermission "localhost:8200", "listen"; };' >> /etc/java-6-openjdk/security/java.policy
echo 'grant {    permission java.net.SocketPermission "localhost:1527", "listen"; };' >> /etc/java-6-openjdk/security/java.policy

#Set the proper time zone for New York
echo "================= Setting TimeZone ================"
echo 'America/New_York' | tee /etc/timezone
dpkg-reconfigure --frontend noninteractive tzdata


#Create the mount for Bigport (not the bigport01 used from windows) for WF Client & PMF installers
mkdir /bigport
mount -t nfs -o ro,intr,sync,soft,vers=2 rediron1:/u1/bigport /bigport

#Create the mounts for the Reporting Server installers 
mkdir /edaport81
mkdir /edaport80
mkdir /edaportHEAD
mount -t nfs -o ro,intr,sync,soft,vers=2 lnxx64r6:/port1/edaport/M727705D/tape/alt_version/tape /edaport80
mount -t nfs -o ro,intr,sync,soft,vers=2 lnxx64r6:/port2/edaport/R727706D/tape/alt_version/tape /edaport81
mount -t nfs -o ro,intr,sync,soft,vers=2 lnxx64r6:/port/edaport/R729999D/tape/alt_version/tape/ /edaportHEAD

#Create the local directory to store installs/preferences
mkdir /installs

#Setup some variables.  These are used to prevent the need to make multiple change for a WF version change
serverMajRel=${reportingServer}
clientMajRel=${majorClient}
clientMinRel=${minorClient}
pmfRel=806
#Where on Bigport?  rels_development or rels_production
relsLoc=rels_development


echo "======================================================================="
echo "====================== Installing Reporting Server ===================="
echo "======================================================================="
#Copy the install file from the NFS share to local install folder
cp /edaport$serverMajRel/i8*.tar /installs
#Untar install file
tar -xf /installs/i8* -C /installs
cd /installs
#Run installer silently
./isetup -inst -m /installs/iserver.tar -e /ibi/srv$serverMajRel/home -license 200-378-1231-61 -edaprfu /ibi/profiles -http_port 8121 -port 8120 -host localhost -approot /ibi/apps -pass vagrant -nostart
if [[ $? -ne 0 ]] ; then
   echo "======================================================================="
   echo "======================================================================="
   echo "Something went wrong in WebFOCUS Server install"
   echo "======================================================================="
   echo "======================================================================="
   exit 1
fi

#Modify EDASTART to add Global variables to disable EDA security and set JDK_HOME
head -n 1 /ibi/srv$serverMajRel/wfs/bin/edastart > /ibi/srv$serverMajRel/wfs/bin/edastart-tmp
echo export EDAEXTSEC=OFF >>/ibi/srv$serverMajRel/wfs/bin/edastart-tmp
echo export JDK_HOME=/usr/lib/jvm/java-6-openjdk-amd64 >>/ibi/srv$serverMajRel/wfs/bin/edastart-tmp
tail -n +2 /ibi/srv$serverMajRel/wfs/bin/edastart >> /ibi/srv$serverMajRel/wfs/bin/edastart-tmp
mv /ibi/srv$serverMajRel/wfs/bin/edastart-tmp /ibi/srv$serverMajRel/wfs/bin/edastart
chmod 777 /ibi/srv$serverMajRel/wfs/bin/edastart

#Copy edastart control script into Ubuntu startup script location
sed "s/srv80/srv$serverMajRel/g" /vagrant/edastart > /etc/init.d/edastart
chmod 755 /etc/init.d/edastart
#Make edastart into a startup process
update-rc.d edastart defaults

#Add tomcat user into EDA user list
echo "admin_id = tomcat7" >> /ibi/profiles/admin.cfg
echo "BEGIN" >> /ibi/profiles/admin.cfg
echo "  admin_level = SRV" >> /ibi/profiles/admin.cfg
echo "END" >> /ibi/profiles/admin.cfg

#Create MySQL adapter and configure for classpath
sed -i 's/\[Adapters\]/\[Adapters\]\\nmysql_jdbdrv = com.mysql.jdbc.Driver\\nmysql_access = y\\nmysql_jdbc = y/' /ibi/srv$serverMajRel/wfs/bin/edaserve.cfg
sed -i 's/CLASS = JAVASERVER/CLASS = JAVASERVER\\nIBI_CLASSPATH = \/var\/lib\/tomcat7\/shared\/mysql.jar:\/var\/lib\/tomcat7\/shared\/derbyclient.jar/' /ibi/srv$serverMajRel/wfs/etc/odin.cfg

#Set the proper code page [Should parameterize for Unicode testing]
cp /vagrant/nlscfg.err /ibi/srv$serverMajRel/wfs/etc

#Copy the pmf silent install properties, replacing the EDA path with the correct path
sed "s/srv80/srv$serverMajRel/g" /vagrant/pmf.properties > /installs/pmf.properties

#Setup proper ownership, copy MySQL JDBC driver into proper location
chown tomcat7:tomcat7 /ibi -R
cp /usr/share/java/mysql.jar /var/lib/tomcat7/shared/
cp /usr/share/java/mysql.jar /usr/share/tomcat7/lib

#Start the reporting server
/etc/init.d/edastart start

echo "======================================================================="
echo "====================== Installing WebFOCUS Client ====================="
echo "======================================================================="
clientRel=$clientMajRel$clientMinRel
#TO BE DONE: If this is using "head" overwrite the clientRel var since it is used for pathing
#clientRel=head

#Get the latest WF Client install and copy to local install folder
#Sometimes the WF client directory name isn't a pure 4 digit number. It sometimes has hf suffix to denote hotfix.case
#So One has to add a wildcard * to the directory, but not the actual instalWebFocusXXXX.bin where XXXX is the 4 digit version number
newestClient=$(ls /bigport/${relsLoc}/${clientRel}*/webfocus | tail -1)
newestClientGen=$(ls /bigport/${relsLoc}/${clientRel}*/webfocus/${newestClient} | tail -1)
copyClientPath=$(cp /bigport/${relsLoc}/${clientRel}*/webfocus/${newestClient}/${newestClientGen}/unix_single_file_pkg/installWebFOCUS${clientRel}.bin /installs)
echo "$copyClientPath"
cd /installs

#Setup the properties file for WF Client silent install
sed "s/WebFOCUS80/WebFOCUS$clientMajRel/g" /vagrant/wf.properties > /installs/wf.properties

#Update pmf silent install properties
sed -i "s/WebFOCUS80/WebFOCUS$clientMajRel/g" /installs/pmf.properties

#Create the WF Repository database in MySQL
mysql -u root -proot -e "create database WebFOCUS8"

#Run the installer
./installWebFOCUS${clientRel}.bin -i silent -f /installs/wf.properties

if [[ $? -ne 0 ]] ; then
   echo "======================================================================="
   echo "======================================================================="
   echo "Something went wrong in WebFOCUS Client install"
   echo "======================================================================="
   echo "======================================================================="
   exit 1
fi

#Setup Tomcat
echo "<?xml version='1.0' encoding='utf-8'?><Context docBase='/ibi/WebFOCUS$clientMajRel/webapps/webfocus' path='/ibi_apps' useHttpOnly='true'></Context>" > /etc/tomcat7/Catalina/localhost/ibi_apps.xml
echo "<?xml version='1.0' encoding='utf-8'?><Context docBase='/ibi/WebFOCUS$clientMajRel/webapps/ibi_html.war' path='/ibi_html' useHttpOnly='true'></Context>" > /etc/tomcat7/Catalina/localhost/ibi_html.xml
echo "<?xml version='1.0' encoding='utf-8'?><Context docBase='/ibi/WebFOCUS$clientMajRel/webapps/ibi_help' path='/ibi_help' useHttpOnly='true'></Context>" > /etc/tomcat7/Catalina/localhost/ibi_help.xml
echo "<?xml version='1.0' encoding='utf-8'?><Context docBase='/ibi/apps' path='/approot' useHttpOnly='true'></Context>" > /etc/tomcat7/Catalina/localhost/approot.xml

#Copy derby drivers into proper location for Tomcat (NOTE that this step may throw an error if derby is not installed with WF)
cp /ibi/derby/lib/derbyclient.jar /var/lib/tomcat7/shared
cp /ibi/derby/lib/derbyclient.jar /usr/share/tomcat7/lib

#Setup WF Client code page
echo "CODE_PAGE = 137" > /ibi/WebFOCUS$clientMajRel/client/wfc/etc/nlscfg.err

#Modify Tomcat start script to have a larger heap space
sed -i 's/-Xmx128M/-Xmx1024M/' /etc/default/tomcat7
sed -i 's/-Xmx128m/-Xmx1024M/' /etc/default/tomcat7


#Add derby start script to Ubuntu startup location and mark it for startup script
cp /vagrant/derby /etc/init.d
update-rc.d derby defaults

echo "======================================================================="
echo "============================ Installing PMF ==========================="
echo "======================================================================="
#Get the latest PMF Release and copy into local install folder
newestClient=`ls /bigport/rels_development/$pmfRel/pmf | tail -1`
newestClientGen=`ls /bigport/rels_development/$pmfRel/pmf/$newestClient | tail -1`
cp /bigport/rels_development/$pmfRel/pmf/$newestClient/$newestClientGen/unix_single_file_pkg/install.bin /installs/pmf-install.bin
cd /installs
chmod 777 pmf-install.bin
# Run the silent install
./pmf-install.bin -i silent -f /installs/pmf.properties
if [[ $? -ne 0 ]] ; then
   echo "======================================================================="
   echo "======================================================================="
   echo "Something went wrong in PMF install"
   echo "======================================================================="
   echo "======================================================================="
   exit 1
fi

echo "======================================================================="
echo "====================== Updating PMF to Trunk =========================="
echo "======================================================================="
#Remove the "external" referenced files since the SVN Checkout process will skip them if they exist
rm /ibi/apps/mainstreet/js/tdgchart-min.js
rm /ibi/apps/mainstreet/jsdebug/tdgchart-min.js
#Preserve the import log just in case
cp /ibi/WebFOCUS$clientMajRel/cm/import/pmf/cm_import_pmf.log /home/vagrant/
rm /ibi/WebFOCUS$clientMajRel/cm/import/pmf -R

#Check out from trunk & revert to the latest in trunk
svn co svn://pmfsvn/trunk/ibi/apps /ibi/apps --force 1>/dev/null
svn co svn://pmfsvn/trunk/ibi/WebFOCUS /ibi/WebFOCUS$clientMajRel --force 1>/dev/null
svn revert /ibi/WebFOCUS$clientMajRel -R
svn revert /ibi/apps -R

#Change the owner of all ibi files and folders to tomcat7
chown tomcat7:tomcat7 /ibi -R

echo "Last configs"

#run a resync bootstrap fex
mkdir /tmp/test
cp /vagrant/bootstrap.fex /tmp/test
cd /tmp/test
/ibi/srv$serverMajRel/wfs/bin/edastart -x ex bootstrap 1>/home/vagrant/out.log

#Startup Tomcat and Apache
chown tomcat7:tomcat7 /ibi -R
/etc/init.d/tomcat7 start
/etc/init.d/apache2 start

IP=`ifconfig eth1 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'`
ENDTIME=$(date +%s)
echo "It took $(($ENDTIME - $STARTTIME)) seconds ($((($ENDTIME - $STARTTIME)/60)) minutes) to complete this task"
echo "Public IP Address: $IP"

#update the loadWF html file to contain the proper URL for this new VM image
sed  "s/localhost/$IP/" /vagrant/loadWF.html.template > /vagrant/loadWF.html""")


def accept_only_integers():
    prompt = None
    while (prompt == None):
        try:
            prompt = int(raw_input())
        except ValueError:
            print("Sorry that is not an acceptable input please try again or exit the program.")
    return prompt


# function responsible for prompting user for OS Choice
def prompt_user_choices():
    # need a seperate os_choice list since the list is built dynamically everytime
    m_os_choice_list = {}
    m_user_os_choice = None
    m_user_server_choice = None
    m_user_client_choice=None
    m_user_majclient_choice = None
    m_user_minclient_choice = None


    # Dynamically build a choice list for Operating System choices
    for i, j in enumerate(OPERATING_SYSTEMS, start=1):
        m_os_choice_list[i] = j

    print "\nPlease select an Operating System :"
    for index, option in m_os_choice_list.items():
        print index, option, OPERATING_SYSTEMS[option]["description"]

    while (m_user_os_choice is None):
        m_user_integer_choice = accept_only_integers()
        try:
            m_user_os_choice = m_os_choice_list[m_user_integer_choice]
        except:
            print("Sorry that is not an acceptable input please try again or exit the program.")
            m_user_os_choice = None

    print "\nPlease select a Reporting Server Version :"
    for key, value in REPORTING_SERVER_OPTIONS.items():
        print key, value
    while (m_user_server_choice is None):
        m_user_integer_choice = accept_only_integers()
        try:
            m_user_server_choice = REPORTING_SERVER_OPTIONS[m_user_integer_choice]
        except:
            print("Sorry that is not an acceptable input please try again or exit the program.")
            m_user_server_choice = None

    print "\nPlease select a Client Major Version:"
    for key, value in DYNAMIC_CLIENT_OPTIONS.items():
        print key, value
    while (m_user_client_choice is None):
        m_user_integer_choice = accept_only_integers()
        try:
            m_user_client_choice = DYNAMIC_CLIENT_OPTIONS[m_user_integer_choice]
        except:
            print("Sorry that is not an acceptable input please try again or exit the program.")
            m_user_client_choice = None

    #The users major and minor client choice are determined by slicing the users client choice
    #The maj client is the first 2 letters while the minor client choice are the preceeding two letters.
    m_user_majclient_choice=m_user_client_choice[0:2]
    m_user_minclient_choice=m_user_client_choice[2:4]





    # mUserOsChoice is a string which represents the users choice for operating system
    # is case sensitive and be aware for underscores
    return (m_user_os_choice, m_user_server_choice, m_user_majclient_choice, m_user_minclient_choice)


    # Opens the Vagrantfile in the directory and writes the specifief options to the file and saves it


def write_settings(m_user_settings):
    m_user_os_choice, m_user_server_choice, m_user_majclient_choice, m_user_minclient_choice = m_user_settings

    print ("...Writing Vagrant Configurations To File...")
    # The next line will open the Vagrant configuration as a file object known as f
    try:
        with open("Vagrantfile", "w+") as f:
            f.write(BASE_VAGRANT_CONFIG.safe_substitute(operating_system=m_user_os_choice))
    except IOError:
        print("Apparently Vagrantfile does not exist.")
    print("Vagrantfile Succesfully Initialized")

    print ("...Writing To Shell Script")
    try:
        with open("bootstrap.sh", "w+") as f:
            f.write(BASE_SHELL_SCRIPT.safe_substitute(reportingServer=m_user_server_choice,
                                                      majorClient=m_user_majclient_choice,
                                                      minorClient=m_user_minclient_choice))
    except IOError:
        print "Error writing to file"
    print ("Shellscript succesfully written")


def query_and_install_boxes(m_currently_installed_boxes):
    # Use the vagrant system object to list out all currently installed boxes and append them to m_currently_installed_boxes
    print "\n System Box Status :"

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
    # connect to bigport on rediron1 to parse client versions
    explore_bigport()
    m_installed_vagrant_boxes = fetch_system_boxes()

    query_and_install_boxes(m_installed_vagrant_boxes)

    m_user_settings = prompt_user_choices()
    write_settings(m_user_settings)


def explore_bigport():
    try:
        path = "//rediron1/u1/bigport/rels_development/"
        print "...Attempting to explore bigport..."

        # lists all directories in the path Z:/bigport/rels_development
        versions = os.listdir(path)
        # remove all possibilites that do not begin with 8 or 7 and are 3 or fewer characters AKA non-client versions
        # this works only for clients that fit the model 8XXX* or 7XXX* where X is a digit and * is a wildcard aka anything
        versions = filter(lambda x: (x[0] == "8" or x[0] == "7") and len(x) > 3, versions)

        for index, item in enumerate(versions, start=1):
            DYNAMIC_CLIENT_OPTIONS[index] = item
        print "Successfully explored bigport built client options."
    except:
        print "There was an error exploring bigport. Please check connections and ensure the drive is mounted and mapped to the letter Z."


if __name__ == "__main__":
    main()
