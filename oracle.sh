#!/bin/bash

echo "Formatting Oracle Server"
cd /ibi/apps/pmfdbms/create_database
echo "exit" | sqlplus system/oracle@localhost:49161 @sqlora_env_defaults.sql
echo "exit" | sqlplus system/oracle@localhost:49161 @sqlora.sql
#EDIT PMF_BASE FOR ORACLE CONFIG

head -n -1 /ibi/profiles/pmf_base.prf >> /ibi/profiles/pmf_basetemp.prf
mv -f /ibi/profiles/pmf_basetemp.prf /ibi/profiles/pmf_base.prf
echo "ENGINE SQLORA SET CONNECTION_ATTRIBUTES pmf_system 'localhost:49161'/system,oracle" >> /ibi/profiles/pmf_base.prf
echo "ENGINE SQLORA SET CONNECTION_ATTRIBUTES pmf_cube 'localhost:49161'/system,oracle" >> /ibi/profiles/pmf_base.prf
echo "ENGINE SQLORA SET CONNECTION_ATTRIBUTES pmf_load_test 'localhost:49161'/system,oracle" >> /ibi/profiles/pmf_base.prf