mysqldump -d -u$1 -p$2 $3 --skip-add-drop-table --skip-comments | sed 's/ AUTO_INCREMENT=[0-9]* / /' | grep -v '^\/\*!40101 SET @saved_cs_client.*\/;$' | grep -v '^\/\*!40101 SET character_set_client.*\/;$' > cato_ddl_tmp.sql


diff cato_ddl.sql cato_ddl_tmp.sql
