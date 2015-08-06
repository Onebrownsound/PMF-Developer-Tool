#!/usr/bin/env bash
#DBCHOICE represents which db will be installed 1->Mysql 2->Postgresql
DBCHOICE=3
#SVNUPDATE whether or not PMF will automatically update to TRUNK on SVN
SVNUPDATE=True

#Setup the start time
STARTTIME=$(date +%s)
#Preset the MySQL root password for use later
sudo debconf-set-selections <<< 'mysql-server-5.5 mysql-server/root_password password root'
sudo debconf-set-selections <<< 'mysql-server-5.5 mysql-server/root_password_again password root'

#Update the packages and install the required ones
sudo apt-get update
sudo apt-get install -y tomcat7 tomcat7-admin vim mysql-server-5.5 apache2 libapache2-mod-jk openjdk-6-jre openjdk-6-jdk libc6 ksh rpm subversion libmysql-java libpostgresql-jdbc-java postgresql postgresql-contrib

if [[ "$DBCHOICE" == "1" ]]; then
    #Create the WF Repository database in MySQL
    mysql -u root -proot -e "create database WebFOCUS8"
elif [[ "$DBCHOICE" == "2" ]]; then
    #Setup postgresql root password for use later
    sudo -u postgres psql -c "ALTER USER postgres with password 'postgres';"
    #Create the WF Repository database in POSTGRESQL
    sudo -u postgres createdb WebFOCUS8
elif [[ "$DBCHOICE" == "3" ]]; then
  #Make Swap file since oracle client requires a somewhat large swap space, set it to 4GB
  sudo fallocate -l 4G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  sudo echo '/swapfile   none    swap    sw    0   0' >> /etc/fstab

  #ORACLE CLIENT INSTALLATION REMEMBER oracle path is hardcoded to opt/oracle/instantclient_11_2
  sudo apt-get install -y unzip libaio1
  sudo mkdir /opt
  sudo mkdir /opt/oracle
  sudo mkdir /opt/oracle/network
  sudo mkdir /opt/oracle/network/admin
  cd /opt/oracle
  sudo unzip /vagrant/instantclient-basic-linux.x64-11.2.0.4.0.zip
  sudo unzip /vagrant/instantclient-sdk-linux.x64-11.2.0.4.0.zip
  sudo unzip /vagrant/instantclient-sqlplus-linux.x64-11.2.0.4.0.zip
  echo export ORACLE_HOME=/opt/oracle >> /etc/profile
  echo export LD_LIBRARY_PATH=/opt/oracle/instantclient_11_2 >> /etc/profile
  echo export PATH=$PATH:/opt/oracle/instantclient_11_2 >> /etc/profile

  #DOCKER Oracle Experimentation
  sudo apt-get install -y docker.io
  sudo docker pull wnameless/oracle-xe-11g
  sudo docker run -d -p 49160:22 -p 49161:1521 wnameless/oracle-xe-11g
else
    echo "There was a problem setting up database credentials check the source script"
    exit 1
fi

#Update Tomcat & Apache for using port 80
sed -i 's/<Connector port="8080"/<Connector port="8009" protocol="AJP\/1.3" redirectPort="8443" \/>\n<Connector port="8080"/' /etc/tomcat7/server.xml
sed -i 's/\/etc\/libapache2-mod-jk\/workers.properties/\/etc\/apache2\/workers.properties/' /etc/apache2/mods-available/jk.conf
cp /vagrant/workers.properties /etc/apache2/workers.properties
cp /vagrant/000-default /etc/apache2/sites-available/default
cp /vagrant/000-default /etc/apache2/sites-available/000-default.conf
/etc/init.d/tomcat7 stop
/etc/init.d/apache2 stop


#Setup java permissions for ReportCaster and Derby to listen on ports 8200 & 1527
echo 'grant {    permission java.net.SocketPermission "localhost:8200", "listen"; };' >> /etc/java-6-openjdk/security/java.policy
echo 'grant {    permission java.net.SocketPermission "localhost:1527", "listen"; };' >> /etc/java-6-openjdk/security/java.policy
echo 'grant codeBase "file:/ibi/apps/mainstreet/batik/-" { permission java.security.AllPermission; };' >> /etc/java-6-openjdk/security/java.policy
echo 'grant codeBase "file:/ibi/apps/mainstreet/java/-" { permission java.security.AllPermission; };' >> /etc/java-6-openjdk/security/java.policy


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
serverMajRel=81
clientMajRel=81
clientMinRel=05
pmfRel=807
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
if [[ "$DBCHOICE" == "3" ]]; then
  #Experimental Oracle stuff
  echo export 'ORACLE_HOME=/opt/oracle' >> /ibi/srv$serverMajRel/wfs/bin/edastart-tmp
  echo export 'PATH=$PATH:/opt/oracle/instantclient_11_2' >> /ibi/srv$serverMajRel/wfs/bin/edastart-tmp
  echo export 'TNS_NAME=/opt/oracle/network/admin' >> /ibi/srv$serverMajRel/wfs/bin/edastart-tmp
  echo export 'LD_LIBRARY_PATH=/opt/oracle/instantclient_11_2' >> /ibi/srv$serverMajRel/wfs/bin/edastart-tmp

  echo export 'ORACLE_SID=xe' >> /ibi/srv$serverMajRel/wfs/bin/edastart-tmp
  echo export 'NLS_LANG=AMERICAN' >> /ibi/srv$serverMajRel/wfs/bin/edastart-tmp
  echo export 'ORA_NCHAR_LITERAL_REPLACE=TRUE' >> /ibi/srv$serverMajRel/wfs/bin/edastart-tmp
fi
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

#Create Adapter based off of DBCHOICE 1:MYSQL 2:POSTGRES
if [[ "$DBCHOICE" == "1" ]]; then
   #Create MySQL adapter and configure for classpath
   sed -i 's/\[Adapters\]/\[Adapters\]\nmysql_jdbdrv = com.mysql.jdbc.Driver\nmysql_access = y\nmysql_jdbc = y/' /ibi/srv$serverMajRel/wfs/bin/edaserve.cfg
   sed -i 's/CLASS = JAVASERVER/CLASS = JAVASERVER\nIBI_CLASSPATH = \/var\/lib\/tomcat7\/shared\/mysql.jar:\/var\/lib\/tomcat7\/shared\/derbyclient.jar/' /ibi/srv$serverMajRel/wfs/etc/odin.cfg
elif [[ "$DBCHOICE" == "2" ]]; then
   #Create Postgresql adapter and configure for classpath
   sed -i 's/\[Adapters\]/\[Adapters\]\npstgr_jdbdrv = org.postgresql.Driver\npstgr_access = y\npstgr_jdbc = y/' /ibi/srv$serverMajRel/wfs/bin/edaserve.cfg
   sed -i 's/CLASS = JAVASERVER/CLASS = JAVASERVER\nIBI_CLASSPATH = \/var\/lib\/tomcat7\/shared\/postgresql.jar:\/var\/lib\/tomcat7\/shared\/derbyclient.jar/' /ibi/srv$serverMajRel/wfs/etc/odin.cfg
elif [[ "$DBCHOICE" == "3" ]]; then
  #Create OracleSQL adapter and configure for classpath
  sed -i 's/\[Adapters\]/\[Adapters\]\nora_access = y\nora_rel = 11\nora_oci = y/' /ibi/srv$serverMajRel/wfs/bin/edaserve.cfg
  sed -i 's/CLASS = JAVASERVER/CLASS = JAVASERVER\nIBI_CLASSPATH = \/var\/lib\/tomcat7\/shared\/ojdbc6.jar:\/var\/lib\/tomcat7\/shared\/derbyclient.jar/' /ibi/srv$serverMajRel/wfs/etc/odin.cfg

else
    echo "There was a problem changing JDBC adapter"
    exit 1
fi

#Set the proper code page [Should parameterize for Unicode testing]
cp /vagrant/nlscfg.err /ibi/srv$serverMajRel/wfs/etc

#Copy the pmf silent install properties, replacing the EDA path with the correct path
sed "s/srv80/srv$serverMajRel/g" /vagrant/pmf.properties > /installs/pmf.properties

#Setup proper ownership, copy MySQL JDBC driver into proper location
chown tomcat7:tomcat7 /ibi -R
cp /usr/share/java/mysql.jar /var/lib/tomcat7/shared/
cp /usr/share/java/mysql.jar /usr/share/tomcat7/lib
cp /usr/share/java/postgresql.jar /var/lib/tomcat7/shared/
cp /usr/share/java/postgresql.jar /usr/share/tomcat7/lib

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


if [[ "$SVNUPDATE" == "True" ]]; then
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
elif [[ "$SVNUPDATE" == "False" ]]; then
    echo "Update on SVN was not elected"
else
    echo "There was a problem regarding SVNUPDATE. Please investigate further or try selecting no with regards to updating PMF via SVN."
    exit 1
fi


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
sed  "s/localhost/$IP/" /vagrant/loadWF.html.template > /vagrant/loadWF.html