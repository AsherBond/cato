
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `action_plan` (
  `plan_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `task_id` varchar(36) NOT NULL,
  `run_on_dt` datetime NOT NULL,
  `action_id` varchar(36) DEFAULT NULL,
  `ecosystem_id` varchar(36) DEFAULT NULL,
  `account_id` varchar(36) DEFAULT NULL,
  `parameter_xml` text,
  `debug_level` int(11) DEFAULT NULL,
  `source` varchar(16) NOT NULL DEFAULT 'manual',
  `schedule_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`plan_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `action_plan_history` (
  `plan_id` bigint(20) NOT NULL,
  `task_id` varchar(36) NOT NULL,
  `run_on_dt` datetime NOT NULL,
  `action_id` varchar(36) DEFAULT NULL,
  `ecosystem_id` varchar(36) DEFAULT NULL,
  `account_id` varchar(36) DEFAULT NULL,
  `parameter_xml` text,
  `debug_level` int(11) DEFAULT NULL,
  `source` varchar(16) NOT NULL DEFAULT 'manual',
  `schedule_id` varchar(36) DEFAULT NULL,
  `task_instance` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`plan_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `action_schedule` (
  `schedule_id` varchar(36) NOT NULL DEFAULT '',
  `task_id` varchar(36) NOT NULL DEFAULT '',
  `action_id` varchar(36) DEFAULT NULL,
  `ecosystem_id` varchar(36) DEFAULT NULL,
  `account_id` varchar(36) DEFAULT NULL,
  `months` varchar(27) DEFAULT NULL,
  `days_or_weeks` int(11) DEFAULT NULL,
  `days` varchar(84) DEFAULT NULL,
  `hours` varchar(62) DEFAULT NULL,
  `minutes` varchar(172) DEFAULT NULL,
  `parameter_xml` text,
  `debug_level` int(11) DEFAULT NULL,
  `label` varchar(64) DEFAULT NULL,
  `descr` varchar(512) DEFAULT NULL,
  `last_modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `modified` int(11) DEFAULT '1',
  PRIMARY KEY (`schedule_id`,`last_modified`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `application_registry` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app_name` varchar(255) NOT NULL DEFAULT '',
  `app_instance` varchar(255) NOT NULL DEFAULT '',
  `master` tinyint(1) NOT NULL,
  `heartbeat` datetime DEFAULT NULL,
  `last_processed_dt` datetime DEFAULT NULL,
  `logfile_name` varchar(255) DEFAULT NULL,
  `load_value` decimal(18,3) DEFAULT NULL,
  `hostname` varchar(255) DEFAULT '',
  `userid` varchar(255) DEFAULT '',
  `pid` int(11) DEFAULT NULL,
  `executible_path` varchar(1024) DEFAULT '',
  `command_line` varchar(255) DEFAULT '',
  `platform` varchar(255) DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `app_name` (`app_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `application_settings` (
  `id` int(11) NOT NULL,
  `setting_xml` text NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `asset` (
  `asset_id` varchar(36) NOT NULL DEFAULT '',
  `asset_name` varchar(255) NOT NULL DEFAULT '',
  `asset_status` varchar(32) NOT NULL,
  `is_connection_system` int(11) NOT NULL,
  `address` varchar(255) DEFAULT '',
  `port` varchar(128) DEFAULT NULL,
  `db_name` varchar(128) DEFAULT NULL,
  `connection_type` varchar(32) DEFAULT NULL,
  `credential_id` varchar(36) DEFAULT NULL,
  `conn_string` text,
  PRIMARY KEY (`asset_id`),
  UNIQUE KEY `asset_IX_asset` (`asset_name`(64))
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `asset_credential` (
  `credential_id` varchar(36) NOT NULL,
  `username` varchar(128) NOT NULL,
  `password` varchar(2048) NOT NULL,
  `domain` varchar(128) DEFAULT NULL,
  `shared_or_local` int(11) NOT NULL,
  `shared_cred_desc` varchar(256) DEFAULT NULL,
  `privileged_password` varchar(512) DEFAULT NULL,
  `credential_name` varchar(64) NOT NULL,
  PRIMARY KEY (`credential_id`),
  UNIQUE KEY `credential_name_UNIQUE` (`credential_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cloud_account` (
  `account_id` varchar(36) NOT NULL,
  `account_name` varchar(64) NOT NULL,
  `account_number` varchar(64) DEFAULT NULL,
  `provider` varchar(16) DEFAULT NULL,
  `login_id` varchar(64) NOT NULL,
  `login_password` varchar(512) NOT NULL,
  `is_default` int(11) NOT NULL,
  `auto_manage_security` int(11) DEFAULT '1',
  `default_cloud_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`account_id`),
  UNIQUE KEY `account_name_UNIQUE` (`account_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `clouds` (
  `cloud_id` varchar(36) NOT NULL,
  `provider` varchar(32) NOT NULL,
  `cloud_name` varchar(32) NOT NULL,
  `api_url` varchar(512) NOT NULL,
  `api_protocol` varchar(8) NOT NULL,
  `default_account_id` varchar(36) DEFAULT NULL,
  `region` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`cloud_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `clouds_keypair` (
  `keypair_id` varchar(36) NOT NULL,
  `cloud_id` varchar(36) NOT NULL,
  `keypair_name` varchar(64) NOT NULL,
  `private_key` varchar(4096) NOT NULL,
  `passphrase` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`cloud_id`,`keypair_name`),
  UNIQUE KEY `keypair_id_UNIQUE` (`keypair_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ecosystem` (
  `ecosystem_id` varchar(36) NOT NULL,
  `ecosystem_name` varchar(64) NOT NULL,
  `account_id` varchar(36) NOT NULL,
  `ecotemplate_id` varchar(36) NOT NULL,
  `ecosystem_desc` varchar(512) DEFAULT NULL,
  `created_dt` datetime DEFAULT NULL,
  `last_update_dt` datetime DEFAULT NULL,
  `parameter_xml` text,
  `storm_file` text,
  `storm_parameter_xml` text,
  `storm_cloud_id` varchar(36) DEFAULT NULL,
  `storm_status` varchar(32) DEFAULT NULL,
  `request_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`ecosystem_id`),
  UNIQUE KEY `name_cloud_account` (`account_id`,`ecosystem_name`),
  KEY `fk_cloud_account` (`account_id`),
  KEY `FK_ecotemplate_id` (`ecotemplate_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ecosystem_log` (
  `ecosystem_log_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `ecosystem_id` varchar(36) NOT NULL,
  `ecosystem_object_type` varchar(32) NOT NULL,
  `logical_id` varchar(256) DEFAULT NULL,
  `ecosystem_object_id` varchar(64) NOT NULL,
  `status` varchar(32) NOT NULL,
  `log` text,
  `update_dt` datetime DEFAULT NULL,
  `event_id` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`ecosystem_log_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ecosystem_object` (
  `ecosystem_id` varchar(36) NOT NULL,
  `cloud_id` varchar(36) NOT NULL,
  `ecosystem_object_id` varchar(64) NOT NULL,
  `ecosystem_object_type` varchar(32) NOT NULL,
  `added_dt` datetime DEFAULT NULL,
  PRIMARY KEY (`ecosystem_id`,`ecosystem_object_id`,`ecosystem_object_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ecosystem_object_tag` (
  `ecosystem_id` varchar(36) NOT NULL,
  `ecosystem_object_id` varchar(64) NOT NULL,
  `key_name` varchar(128) NOT NULL,
  `value` varchar(256) NOT NULL,
  PRIMARY KEY (`ecosystem_id`,`ecosystem_object_id`,`key_name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ecosystem_output` (
  `ecosystem_id` varchar(36) NOT NULL,
  `output_key` varchar(32) NOT NULL,
  `output_desc` varchar(256) DEFAULT NULL,
  `output_value` varchar(1024) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ecotemplate` (
  `ecotemplate_id` varchar(36) NOT NULL,
  `ecotemplate_name` varchar(64) DEFAULT NULL,
  `ecotemplate_desc` varchar(512) DEFAULT NULL,
  `storm_file_type` varchar(8) DEFAULT NULL,
  `storm_file` text,
  PRIMARY KEY (`ecotemplate_id`),
  UNIQUE KEY `ecotemplate_name` (`ecotemplate_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ecotemplate_action` (
  `action_id` varchar(36) NOT NULL,
  `ecotemplate_id` varchar(36) NOT NULL,
  `action_name` varchar(64) NOT NULL,
  `action_desc` varchar(512) DEFAULT NULL,
  `category` varchar(32) DEFAULT NULL,
  `original_task_id` varchar(36) DEFAULT NULL,
  `task_version` decimal(18,3) DEFAULT NULL,
  `parameter_defaults` text,
  `action_icon` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`action_id`),
  UNIQUE KEY `template_action` (`ecotemplate_id`,`action_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ecotemplate_runlist` (
  `item_id` varchar(36) NOT NULL,
  `ecotemplate_id` varchar(36) NOT NULL,
  `item_type` varchar(32) NOT NULL,
  `item_order` int(11) NOT NULL,
  `item_notes` varchar(2048) DEFAULT NULL,
  `account_id` varchar(36) DEFAULT NULL,
  `cloud_id` varchar(36) DEFAULT NULL,
  `image_id` varchar(36) DEFAULT NULL,
  `source` varchar(1024) DEFAULT NULL,
  `data` text,
  PRIMARY KEY (`item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `image` (
  `image_id` varchar(36) NOT NULL,
  `image_type` varchar(32) NOT NULL,
  `image_name` varchar(256) NOT NULL,
  `image_desc` varchar(2048) DEFAULT NULL,
  `account_id` varchar(36) DEFAULT NULL,
  `cloud_id` varchar(36) DEFAULT NULL,
  `external_id` varchar(256) DEFAULT NULL,
  `source` varchar(1024) DEFAULT NULL,
  `data` text,
  PRIMARY KEY (`image_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ldap_domain` (
  `ldap_domain` varchar(255) NOT NULL DEFAULT '',
  `address` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`ldap_domain`(64))
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `login_security_settings` (
  `id` int(11) NOT NULL,
  `pass_max_age` int(11) NOT NULL,
  `pass_max_attempts` int(11) NOT NULL,
  `pass_max_length` int(11) NOT NULL,
  `pass_min_length` int(11) NOT NULL,
  `pass_complexity` int(11) NOT NULL,
  `pass_age_warn_days` int(11) NOT NULL,
  `pass_require_initial_change` int(11) NOT NULL,
  `auto_lock_reset` int(11) NOT NULL,
  `login_message` varchar(255) NOT NULL DEFAULT '',
  `auth_error_message` varchar(255) NOT NULL DEFAULT '',
  `pass_history` int(11) NOT NULL,
  `page_view_logging` int(11) NOT NULL,
  `report_view_logging` int(11) NOT NULL,
  `allow_login` int(11) NOT NULL,
  `new_user_email_message` varchar(1024) DEFAULT NULL,
  `log_days` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `message` (
  `msg_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `date_time_entered` datetime DEFAULT NULL,
  `date_time_completed` datetime DEFAULT NULL,
  `process_id` int(11) DEFAULT NULL,
  `process_type` int(11) DEFAULT NULL,
  `status` int(11) DEFAULT NULL,
  `error_message` varchar(255) DEFAULT '',
  `msg_to` varchar(255) DEFAULT '',
  `msg_from` varchar(255) DEFAULT '',
  `msg_subject` varchar(255) DEFAULT '',
  `msg_body` text,
  `retry` int(11) DEFAULT NULL,
  `num_retries` int(11) DEFAULT NULL,
  `msg_cc` varchar(255) DEFAULT '',
  `msg_bcc` varchar(255) DEFAULT '',
  PRIMARY KEY (`msg_id`),
  KEY `message_IX_message` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `message_data_file` (
  `msg_file_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `msg_id` bigint(20) DEFAULT NULL,
  `file_name` varchar(255) DEFAULT NULL,
  `file_type` int(11) DEFAULT NULL,
  `file_data` blob,
  PRIMARY KEY (`msg_file_id`),
  KEY `FK_message_data_file_message` (`msg_id`),
  CONSTRAINT `FK_message_data_file_message` FOREIGN KEY (`msg_id`) REFERENCES `message` (`msg_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `message_file_lookup` (
  `file_type` int(11) NOT NULL AUTO_INCREMENT,
  `file_description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`file_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `messenger_settings` (
  `id` int(11) NOT NULL,
  `mode_off_on` varchar(3) NOT NULL,
  `loop_delay_sec` int(11) NOT NULL,
  `retry_delay_min` int(11) NOT NULL,
  `retry_max_attempts` int(11) NOT NULL,
  `smtp_server_addr` varchar(255) DEFAULT '',
  `smtp_server_user` varchar(255) DEFAULT '',
  `smtp_server_password` varchar(255) DEFAULT '1753-01-01 00:00:00',
  `smtp_server_port` int(11) DEFAULT NULL,
  `from_email` varchar(255) DEFAULT '',
  `from_name` varchar(255) DEFAULT '',
  `admin_email` varchar(255) DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `object_registry` (
  `object_id` varchar(36) NOT NULL,
  `registry_xml` text NOT NULL,
  PRIMARY KEY (`object_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `object_tags` (
  `object_id` varchar(36) NOT NULL,
  `object_type` int(11) NOT NULL,
  `tag_name` varchar(32) NOT NULL,
  PRIMARY KEY (`object_id`,`tag_name`,`object_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `poller_settings` (
  `id` int(11) NOT NULL,
  `mode_off_on` varchar(3) NOT NULL,
  `loop_delay_sec` int(11) NOT NULL,
  `max_processes` int(11) NOT NULL,
  `app_instance` varchar(1024) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `request` (
  `request_id` varchar(36) NOT NULL,
  `request_status` varchar(32) NOT NULL,
  `request_desc` varchar(256) NOT NULL,
  `requestor_id` varchar(36) NOT NULL,
  `request_dt` datetime NOT NULL,
  `start_dt` datetime DEFAULT NULL,
  `end_dt` datetime DEFAULT NULL,
  `request_notes` text,
  `approved_dt` datetime DEFAULT NULL,
  `approver_id` varchar(36) DEFAULT NULL,
  `approval_notes` text,
  PRIMARY KEY (`request_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `request_item` (
  `item_id` varchar(36) NOT NULL,
  `request_id` varchar(36) NOT NULL,
  `item_order` int(11) NOT NULL,
  `image_id` varchar(36) NOT NULL,
  `item_notes` varchar(2048) DEFAULT NULL,
  PRIMARY KEY (`item_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `scheduler_settings` (
  `id` int(11) NOT NULL,
  `mode_off_on` varchar(3) NOT NULL,
  `loop_delay_sec` int(11) NOT NULL,
  `schedule_min_depth` int(11) NOT NULL,
  `schedule_max_days` int(11) NOT NULL,
  `clean_app_registry` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tags` (
  `tag_name` varchar(32) NOT NULL,
  `tag_desc` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`tag_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task` (
  `task_id` varchar(36) NOT NULL DEFAULT '',
  `original_task_id` varchar(36) NOT NULL DEFAULT '',
  `version` decimal(18,3) NOT NULL,
  `task_name` varchar(255) NOT NULL DEFAULT '',
  `task_code` varchar(32) DEFAULT NULL,
  `task_desc` varchar(255) DEFAULT '',
  `task_status` varchar(32) NOT NULL DEFAULT 'Development',
  `use_connector_system` int(11) NOT NULL DEFAULT '0',
  `default_version` int(11) NOT NULL,
  `concurrent_instances` int(11) DEFAULT NULL,
  `queue_depth` int(11) DEFAULT NULL,
  `created_dt` datetime NOT NULL,
  `parameter_xml` text NOT NULL,
  PRIMARY KEY (`task_id`),
  UNIQUE KEY `IX_task_version` (`original_task_id`,`version`),
  UNIQUE KEY `IX_task_name_version` (`task_name`(64),`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task_codeblock` (
  `task_id` varchar(36) NOT NULL DEFAULT '',
  `codeblock_name` varchar(32) NOT NULL DEFAULT '',
  PRIMARY KEY (`task_id`,`codeblock_name`),
  KEY `FK_task_codeblock_task` (`task_id`),
  CONSTRAINT `FK_task_codeblock_task` FOREIGN KEY (`task_id`) REFERENCES `task` (`task_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task_conn_log` (
  `task_instance` bigint(20) NOT NULL,
  `address` varchar(128) NOT NULL,
  `userid` varchar(36) DEFAULT '',
  `conn_type` varchar(32) NOT NULL,
  `conn_dt` datetime NOT NULL,
  KEY `IX_task_conn_log_address` (`address`(64)),
  KEY `IX_task_conn_log_conn_dt` (`conn_dt`),
  KEY `IX_task_conn_log_ti` (`task_instance`),
  KEY `IX_task_conn_log_userid` (`userid`(32))
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task_instance` (
  `task_instance` bigint(20) NOT NULL AUTO_INCREMENT,
  `task_id` varchar(36) NOT NULL DEFAULT '',
  `task_status` varchar(16) NOT NULL,
  `debug_level` int(11) NOT NULL DEFAULT '0',
  `asset_id` varchar(36) DEFAULT '',
  `submitted_by` varchar(36) DEFAULT '',
  `submitted_dt` datetime DEFAULT NULL,
  `started_dt` datetime DEFAULT NULL,
  `completed_dt` datetime DEFAULT NULL,
  `schedule_instance` bigint(20) DEFAULT NULL,
  `ce_node` int(11) DEFAULT NULL,
  `pid` int(11) DEFAULT NULL,
  `group_name` varchar(32) DEFAULT NULL,
  `submitted_by_instance` bigint(20) DEFAULT NULL,
  `ecosystem_id` varchar(36) DEFAULT NULL,
  `account_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`task_instance`),
  KEY `IX_task_instance_asset_id` (`asset_id`),
  KEY `IX_task_instance_cenode` (`ce_node`),
  KEY `IX_task_instance_completed_dt` (`completed_dt`),
  KEY `IX_task_instance_started_dt` (`started_dt`),
  KEY `IX_task_instance_status_pid` (`task_status`,`pid`),
  KEY `IX_task_instance_task_id` (`task_id`),
  KEY `IX_task_instance_task_status` (`task_status`),
  KEY `IX_task_instance_schedule_instance` (`schedule_instance`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task_instance_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_instance` bigint(20) NOT NULL,
  `step_id` varchar(36) DEFAULT '',
  `entered_dt` datetime DEFAULT NULL,
  `connection_name` varchar(36) DEFAULT NULL,
  `log` mediumtext,
  `command_text` text,
  PRIMARY KEY (`id`),
  KEY `task_instance_log_IX_task_instance_log` (`task_instance`,`entered_dt`),
  KEY `IX_task_instance_log_connection_name` (`connection_name`),
  CONSTRAINT `FK_task_instance_log_task_instance` FOREIGN KEY (`task_instance`) REFERENCES `task_instance` (`task_instance`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task_instance_parameter` (
  `task_instance` bigint(20) NOT NULL,
  `parameter_xml` text NOT NULL,
  PRIMARY KEY (`task_instance`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task_step` (
  `step_id` varchar(36) NOT NULL DEFAULT '',
  `task_id` varchar(36) NOT NULL DEFAULT '',
  `codeblock_name` varchar(36) NOT NULL DEFAULT '',
  `step_order` int(11) NOT NULL,
  `commented` int(11) NOT NULL DEFAULT '0',
  `locked` int(11) NOT NULL DEFAULT '0',
  `function_name` varchar(64) NOT NULL,
  `function_xml` text NOT NULL,
  `step_desc` varchar(255) DEFAULT '',
  PRIMARY KEY (`step_id`),
  KEY `task_step_IX_task_step` (`task_id`,`codeblock_name`,`commented`),
  KEY `IX_task_step_commented` (`commented`),
  KEY `IX_task_step_function_name` (`function_name`),
  CONSTRAINT `FK_task_step_task` FOREIGN KEY (`task_id`) REFERENCES `task` (`task_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task_step_clipboard` (
  `user_id` varchar(36) NOT NULL DEFAULT '',
  `clip_dt` datetime NOT NULL,
  `src_step_id` varchar(36) NOT NULL DEFAULT '',
  `root_step_id` varchar(36) NOT NULL DEFAULT '',
  `step_id` varchar(36) NOT NULL DEFAULT '',
  `function_name` varchar(32) NOT NULL,
  `function_xml` text NOT NULL,
  `step_desc` varchar(255) DEFAULT '',
  `codeblock_name` varchar(36) DEFAULT NULL,
  KEY `user_id` (`user_id`,`clip_dt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `task_step_user_settings` (
  `user_id` varchar(36) NOT NULL DEFAULT '',
  `step_id` varchar(36) NOT NULL DEFAULT '',
  `visible` int(11) NOT NULL,
  `breakpoint` int(11) NOT NULL,
  `skip` int(11) NOT NULL,
  `button` varchar(16) DEFAULT NULL,
  PRIMARY KEY (`user_id`,`step_id`),
  KEY `FK_task_step_user_settings_task_step` (`step_id`),
  KEY `FK_task_step_user_settings_users` (`user_id`),
  CONSTRAINT `FK_task_step_user_settings_task_step` FOREIGN KEY (`step_id`) REFERENCES `task_step` (`step_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `FK_task_step_user_settings_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_password_history` (
  `user_id` varchar(36) NOT NULL DEFAULT '',
  `change_time` datetime NOT NULL DEFAULT '1753-01-01 00:00:00',
  `password` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`user_id`,`change_time`),
  KEY `FK_user_password_history_users` (`user_id`),
  CONSTRAINT `FK_user_password_history_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_security_log` (
  `log_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `log_type` varchar(16) NOT NULL,
  `action` varchar(32) NOT NULL,
  `user_id` varchar(36) NOT NULL DEFAULT '',
  `log_dt` datetime NOT NULL,
  `object_type` int(11) DEFAULT NULL,
  `object_id` varchar(255) DEFAULT '',
  `log_msg` varchar(255) DEFAULT '',
  PRIMARY KEY (`log_id`),
  KEY `IX_user_security_log_log_dt` (`log_dt`),
  KEY `IX_user_security_log_log_type` (`log_type`),
  KEY `IX_user_security_log_object_id` (`object_id`(64)),
  KEY `IX_user_security_log_user_id` (`user_id`),
  KEY `FK_user_security_log_users` (`user_id`),
  CONSTRAINT `FK_user_security_log_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_session` (
  `user_id` varchar(36) NOT NULL DEFAULT '',
  `address` varchar(255) NOT NULL DEFAULT '',
  `login_dt` datetime NOT NULL,
  `heartbeat` datetime NOT NULL,
  `kick` int(11) NOT NULL,
  PRIMARY KEY (`user_id`,`address`),
  KEY `FK_user_session_users` (`user_id`),
  CONSTRAINT `FK_user_session_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `user_id` varchar(36) NOT NULL DEFAULT '',
  `username` varchar(128) NOT NULL,
  `full_name` varchar(255) NOT NULL DEFAULT '',
  `status` int(11) NOT NULL,
  `authentication_type` varchar(16) NOT NULL,
  `user_password` varchar(255) DEFAULT '1753-01-01 00:00:00',
  `expiration_dt` datetime DEFAULT NULL,
  `security_question` varchar(255) DEFAULT NULL,
  `security_answer` varchar(255) DEFAULT NULL,
  `last_login_dt` datetime DEFAULT NULL,
  `failed_login_attempts` int(11) DEFAULT NULL,
  `force_change` int(11) DEFAULT NULL,
  `email` varchar(255) DEFAULT '',
  `settings_xml` text,
  `user_role` varchar(32) NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `users_IX_users` (`username`(64))
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

