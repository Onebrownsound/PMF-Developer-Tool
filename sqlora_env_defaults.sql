--  This is sqlora_env_defaults.sql
--  It creates required Oracle table spaces and a default OWNER/SCHEMA
--  NOTE:
--      It is recommended that these scripts be run by an experienced Oracle DBA person.
--      If such a person is not available, then at a minimum please have the Oracle DBA 
--      review these scripts before running them to make sure they meet the site standards.
--
--      This script must be run using an ID that has DBA authority
--      If you get messages that resemble this:
--
--                         from DBA_TABLES
--                              *
--         ERROR at line 6:
--         ORA-06550: line 6, column 22: 
--         PL/SQL: ORA-00942: table or view does not exist 
--         ORA-06550: line 5, column 16: 
--         PL/SQL: SQL Statement ignored
--
--   then you are not running with the proper ID.
--
--   You may set echo & verify on to assist in debugging
set echo   off
set verify off

undefine PMF_DB_OWNER
undefine PMF_DB_FILE_LOC
undefine PMF_DB_TABLESPACE
undefine PMF_DB_INDEXSPACE

define PMF_DB_OWNER     = PMF
define PMF_DB_FILE_LOC  = "C:\Oracle\product\10.2.0\oradata\PMF\"
define PMF_DB_TABLESPACE = PMF_DATAMART_DATA
define PMF_DB_INDEXSPACE = PMF_DATAMART_INDEX 

declare 
   pmf_tablespace_name  varchar2(30) := upper('&&PMF_DB_TABLESPACE');
begin 
   for trec in (select null 
                from dba_tablespaces 
                where TABLESPACE_NAME = pmf_tablespace_name) 
   loop 
      execute immediate 'drop tablespace ' || pmf_tablespace_name || ' including contents and datafiles ' ; 
   end loop; 
end; 
/

--       NOTE:
--       This creates the PMF tablespaces in a default file directory/folder.
--       The most typical default location on WINNT machines is [ORACLE_HOME]\database

--       Alternatively, you may identify a specific folder.
--       On WinNT this is typically [ORACLE_HOME]\oradata\[ORACLE_SID]
--       You may also further modify this DDL to whatever physical characteristics you deem appropriate.

create tablespace &&PMF_DB_TABLESPACE
   datafile '&&PMF_DB_TABLESPACE..dbf'
--   datafile '&&PMF_DB_FILE_LOC.&&PMF_DB_TABLESPACE..dbf'
   size 10M 
   autoextend
   on next 10M
/

declare 
   pmf_tablespace_name  varchar2(30) := upper('&&PMF_DB_INDEXSPACE');
begin 
   for trec in (select null 
                from dba_tablespaces 
                where TABLESPACE_NAME = pmf_tablespace_name) 
   loop 
      execute immediate 'drop tablespace ' || pmf_tablespace_name || ' including contents and datafiles ' ; 
   end loop; 
end; 
/

create tablespace &PMF_DB_INDEXSPACE
   datafile '&&PMF_DB_INDEXSPACE..dbf'
--   datafile '&&PMF_DB_FILE_LOC.&&PMF_DB_INDEXSPACE..dbf'
   size 10M 
   autoextend
   on next 10M 
/

drop user &&PMF_DB_OWNER cascade
/
create user &&PMF_DB_OWNER 
   identified by &&PMF_DB_OWNER
/
alter user &&PMF_DB_OWNER
   quota unlimited on &&PMF_DB_TABLESPACE
   quota unlimited on &&PMF_DB_INDEXSPACE
/
grant create session to &&PMF_DB_OWNER
/
grant dba to &&PMF_DB_OWNER
/
--  If DBA is not grsnted, then give explicit permission to create & drop public synonyms
grant create public synonym to &&PMF_DB_OWNER
/
grant drop public synonym to &&PMF_DB_OWNER
/


commit
/
