mysqldump -d -u$1 -p$2 $3 --skip-add-drop-table --skip-comments | sed 's/ AUTO_INCREMENT=[0-9]* / /' | grep -v '^\/\*!40101 SET @saved_cs_client.*\/;$' | grep -v '^\/\*!40101 SET character_set_client.*\/;$' > /tmp/cato_ddl_tmp.sql


diff $CSK_HOME/cato/install/cato_ddl.sql /tmp/cato_ddl_tmp.sql
