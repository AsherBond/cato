
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
CREATE TABLE `action_plan` (
  `plan_id` bigint(20) NOT NULL AUTO_INCREMENT,
  `task_id` varchar(36) NOT NULL,
  `run_on_dt` datetime NOT NULL,
  `action_id` varchar(36) DEFAULT NULL,
  `ecosystem_id` varchar(36) DEFAULT NULL,
  `account_id` varchar(36) DEFAULT NULL,
  `parameter_xml` mediumtext NOT NULL,
  `debug_level` int(11) DEFAULT NULL,
  `source` varchar(16) NOT NULL DEFAULT 'manual',
  `schedule_id` varchar(36) DEFAULT NULL,
  `cloud_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`plan_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `action_plan_history` (
  `plan_id` bigint(20) NOT NULL,
  `task_id` varchar(36) NOT NULL,
  `run_on_dt` datetime NOT NULL,
  `action_id` varchar(36) DEFAULT NULL,
  `ecosystem_id` varchar(36) DEFAULT NULL,
  `account_id` varchar(36) DEFAULT NULL,
  `parameter_xml` mediumtext NOT NULL,
  `debug_level` int(11) DEFAULT NULL,
  `source` varchar(16) NOT NULL DEFAULT 'manual',
  `schedule_id` varchar(36) DEFAULT NULL,
  `task_instance` bigint(20) DEFAULT NULL,
  `cloud_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`plan_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
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
  `parameter_xml` mediumtext NOT NULL,
  `debug_level` int(11) DEFAULT NULL,
  `label` varchar(64) DEFAULT NULL,
  `descr` varchar(512) DEFAULT NULL,
  `last_modified` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `modified` int(11) DEFAULT '1',
  `cloud_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`schedule_id`,`last_modified`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `api_tokens` (
  `user_id` varchar(36) NOT NULL,
  `token` varchar(36) NOT NULL,
  `created_dt` datetime NOT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
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
CREATE TABLE `application_settings` (
  `id` int(11) NOT NULL,
  `setting_xml` text NOT NULL,
  `license` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
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
CREATE TABLE `clouds` (
  `cloud_id` varchar(36) NOT NULL,
  `provider` varchar(32) NOT NULL,
  `cloud_name` varchar(32) NOT NULL,
  `api_url` varchar(512) NOT NULL,
  `api_protocol` varchar(8) NOT NULL,
  `default_account_id` varchar(36) DEFAULT NULL,
  `region` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`cloud_id`),
  UNIQUE KEY `CLOUD_NAME` (`cloud_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `clouds_keypair` (
  `keypair_id` varchar(36) NOT NULL,
  `cloud_id` varchar(36) NOT NULL,
  `keypair_name` varchar(64) NOT NULL,
  `private_key` varchar(4096) NOT NULL,
  `passphrase` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`cloud_id`,`keypair_name`),
  UNIQUE KEY `keypair_id_UNIQUE` (`keypair_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `dep_action_inst` (
  `action_id` varchar(36) NOT NULL,
  `task_instance` bigint(20) NOT NULL,
  `status` varchar(32) NOT NULL,
  `instance_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`action_id`,`task_instance`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `dep_seq_inst` (
  `seq_instance` bigint(20) NOT NULL AUTO_INCREMENT,
  `sequence_id` varchar(36) NOT NULL,
  `deployment_id` varchar(36) NOT NULL,
  `status` varchar(16) NOT NULL,
  `on_error` varchar(16) NOT NULL DEFAULT 'pause',
  `submitted_dt` datetime DEFAULT NULL,
  `submitted_by` varchar(36) DEFAULT '',
  `completed_dt` datetime DEFAULT NULL,
  `current_step` int(11) DEFAULT NULL,
  `params_def` text,
  `params_vals` text,
  `pid` int(11) DEFAULT NULL,
  PRIMARY KEY (`seq_instance`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `dep_seq_inst_step` (
  `seq_instance` bigint(20) NOT NULL,
  `step_number` int(11) NOT NULL,
  `status` varchar(16) NOT NULL,
  PRIMARY KEY (`seq_instance`,`step_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `dep_seq_inst_step_svc` (
  `seq_instance` bigint(20) NOT NULL,
  `step_number` int(11) NOT NULL,
  `deployment_service_id` varchar(36) NOT NULL,
  `status` varchar(32) NOT NULL,
  `original_task_id` varchar(36) NOT NULL,
  `task_version` varchar(16) NOT NULL,
  PRIMARY KEY (`seq_instance`,`step_number`,`deployment_service_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `dep_seq_inst_svc` (
  `seq_instance` bigint(20) NOT NULL,
  `deployment_service_id` varchar(36) NOT NULL,
  PRIMARY KEY (`seq_instance`,`deployment_service_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `dep_seq_inst_tran` (
  `seq_instance` bigint(20) NOT NULL,
  `step_number` int(11) NOT NULL,
  `deployment_service_id` varchar(36) NOT NULL,
  `instance_id` varchar(36) NOT NULL,
  `instance_label` varchar(80) NOT NULL,
  `task_instance` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`seq_instance`,`step_number`,`deployment_service_id`,`instance_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `dep_seq_params` (
  `sequence_id` varchar(36) NOT NULL,
  `params_def` text NOT NULL,
  `params_vals` text NOT NULL,
  PRIMARY KEY (`sequence_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `dep_seq_tran_params` (
  `sequence_id` varchar(36) NOT NULL,
  `step_number` int(11) NOT NULL,
  `deployment_service_id` varchar(36) NOT NULL,
  `parameter_xml` mediumtext NOT NULL,
  PRIMARY KEY (`sequence_id`,`step_number`,`deployment_service_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `dep_service_inst_mon` (
  `instance_id` varchar(36) NOT NULL,
  `schedule_id` varchar(36) NOT NULL,
  PRIMARY KEY (`instance_id`,`schedule_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `dep_service_inst_proc` (
  `instance_id` varchar(36) NOT NULL,
  `proc_name` varchar(32) NOT NULL,
  `desired_count` int(11) DEFAULT NULL,
  PRIMARY KEY (`instance_id`,`proc_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `dep_service_inst_proc_inst` (
  `instance_id` varchar(36) NOT NULL,
  `proc_name` varchar(32) NOT NULL,
  `pid` int(11) NOT NULL DEFAULT '0',
  `start_dt` datetime DEFAULT NULL,
  PRIMARY KEY (`instance_id`,`proc_name`,`pid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `dep_service_state_mon` (
  `deployment_service_id` varchar(36) NOT NULL,
  `state` varchar(16) NOT NULL,
  `original_task_id` varchar(36) NOT NULL DEFAULT '',
  `task_version` varchar(16) DEFAULT NULL,
  `months` varchar(27) DEFAULT NULL,
  `days_or_weeks` int(11) DEFAULT NULL,
  `days` varchar(84) DEFAULT NULL,
  `hours` varchar(62) DEFAULT NULL,
  `minutes` varchar(172) DEFAULT NULL,
  PRIMARY KEY (`deployment_service_id`,`state`,`original_task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `dep_template_category` (
  `category_id` varchar(36) NOT NULL,
  `category_name` varchar(32) NOT NULL,
  `icon` mediumblob,
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `category_name_UNIQUE` (`category_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `deployment` (
  `deployment_id` varchar(36) NOT NULL,
  `deployment_name` varchar(64) NOT NULL,
  `template_id` varchar(36) NOT NULL,
  `document_id` varchar(24) NOT NULL,
  `status` varchar(16) DEFAULT NULL,
  `owner_user_id` varchar(36) DEFAULT NULL,
  `deployment_desc` varchar(512) DEFAULT NULL,
  `health` varchar(16) DEFAULT 'unknown',
  `runstate` varchar(16) DEFAULT NULL,
  `expiration_dt` datetime DEFAULT NULL,
  `uptime` varchar(45) DEFAULT NULL,
  `archive` int(11) DEFAULT NULL,
  `prompts` text,
  `options` text,
  `created_dt` datetime NOT NULL,
  PRIMARY KEY (`deployment_id`),
  UNIQUE KEY `environment_name_UNIQUE` (`deployment_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `deployment_action` (
  `action_id` varchar(36) NOT NULL,
  `action_name` varchar(64) NOT NULL,
  `scope` int(11) NOT NULL,
  `deployment_id` varchar(36) NOT NULL,
  `deployment_service_id` varchar(36) DEFAULT NULL,
  `action_icon` varchar(32) DEFAULT NULL,
  `action_desc` varchar(512) DEFAULT NULL,
  `category` varchar(32) DEFAULT NULL,
  `original_task_id` varchar(36) DEFAULT NULL,
  `task_version` decimal(18,3) DEFAULT NULL,
  `parameter_defaults` text,
  PRIMARY KEY (`action_id`),
  UNIQUE KEY `service_action` (`action_name`,`deployment_id`,`deployment_service_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `deployment_host` (
  `deployment_id` varchar(36) NOT NULL,
  `host_id` varchar(36) NOT NULL,
  `host_name` varchar(128) NOT NULL,
  `address` varchar(128) DEFAULT NULL,
  `up_dt` datetime DEFAULT NULL,
  PRIMARY KEY (`deployment_id`,`host_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `deployment_log` (
  `log_id` int(11) NOT NULL AUTO_INCREMENT,
  `log_dt` datetime NOT NULL,
  `deployment_id` varchar(36) NOT NULL,
  `deployment_service_id` varchar(36) DEFAULT NULL,
  `instance_id` varchar(36) DEFAULT NULL,
  `seq_instance` bigint(20) DEFAULT NULL,
  `step_number` int(11) DEFAULT NULL,
  `action_id` varchar(36) DEFAULT NULL,
  `task_instance` bigint(20) DEFAULT NULL,
  `log_msg` text,
  PRIMARY KEY (`log_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `deployment_sequence` (
  `sequence_id` varchar(36) NOT NULL,
  `deployment_id` varchar(36) NOT NULL,
  `sequence_name` varchar(32) NOT NULL,
  `sequence_desc` varchar(255) DEFAULT NULL,
  `icon` varchar(64) DEFAULT NULL,
  `prompts` text,
  PRIMARY KEY (`sequence_id`),
  UNIQUE KEY `sequence_name_deployment` (`deployment_id`,`sequence_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `deployment_service` (
  `deployment_id` varchar(36) NOT NULL,
  `deployment_service_id` varchar(36) NOT NULL,
  `service_name` varchar(64) NOT NULL,
  `document_id` varchar(24) NOT NULL,
  `service_desc` varchar(255) DEFAULT NULL,
  `health` varchar(16) DEFAULT 'unknown',
  `options` text,
  PRIMARY KEY (`deployment_id`,`deployment_service_id`),
  UNIQUE KEY `service_name_deployment_id` (`deployment_id`,`service_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `deployment_service_inst` (
  `deployment_service_id` varchar(36) NOT NULL,
  `instance_id` varchar(36) NOT NULL,
  `instance_label` varchar(80) NOT NULL,
  `instance_num` int(11) DEFAULT NULL,
  `status` varchar(16) NOT NULL,
  `current_state` varchar(16) DEFAULT NULL,
  `cloud_id` varchar(36) DEFAULT NULL,
  `cloud_account_id` varchar(36) DEFAULT NULL,
  `host_id` varchar(36) DEFAULT NULL,
  `seq_instance` bigint(20) DEFAULT NULL,
  `run_level` int(11) DEFAULT NULL,
  PRIMARY KEY (`instance_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `deployment_step` (
  `sequence_id` varchar(36) NOT NULL,
  `step_number` int(11) NOT NULL,
  PRIMARY KEY (`sequence_id`,`step_number`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `deployment_step_service` (
  `sequence_id` varchar(36) NOT NULL,
  `step_number` int(11) NOT NULL,
  `deployment_service_id` varchar(36) NOT NULL,
  `original_task_id` varchar(36) DEFAULT NULL,
  `task_version` varchar(36) DEFAULT NULL,
  `desired_state` varchar(16) DEFAULT NULL,
  `run_level` varchar(36) DEFAULT NULL,
  `json` text,
  PRIMARY KEY (`sequence_id`,`step_number`,`deployment_service_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `deployment_template` (
  `template_id` varchar(36) NOT NULL,
  `template_name` varchar(64) NOT NULL,
  `template_version` varchar(8) NOT NULL,
  `template_desc` varchar(1024) DEFAULT NULL,
  `template_text` mediumtext NOT NULL,
  `icon` mediumblob,
  `categories` varchar(1024) DEFAULT NULL,
  `svc_count` int(11) DEFAULT '0',
  `available` int(11) DEFAULT '0',
  PRIMARY KEY (`template_id`),
  UNIQUE KEY `name_version` (`template_name`,`template_version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `ldap_domain` (
  `ldap_domain` varchar(255) NOT NULL DEFAULT '',
  `address` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`ldap_domain`(64))
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
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
CREATE TABLE `marshaller_settings` (
  `id` int(11) NOT NULL,
  `mode_off_on` varchar(3) NOT NULL,
  `loop_delay_sec` int(11) NOT NULL,
  `debug` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
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
CREATE TABLE `message_file_lookup` (
  `file_type` int(11) NOT NULL AUTO_INCREMENT,
  `file_description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`file_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `messenger_settings` (
  `id` int(11) NOT NULL,
  `mode_off_on` varchar(3) NOT NULL,
  `loop_delay_sec` int(11) NOT NULL,
  `retry_delay_min` int(11) NOT NULL,
  `retry_max_attempts` int(11) NOT NULL,
  `smtp_server_addr` varchar(255) DEFAULT '',
  `smtp_server_user` varchar(255) DEFAULT '',
  `smtp_server_password` varchar(255) DEFAULT NULL,
  `smtp_server_port` int(11) DEFAULT NULL,
  `smtp_timeout` int(11) DEFAULT NULL,
  `smtp_ssl` int(11) DEFAULT NULL,
  `from_email` varchar(255) DEFAULT '',
  `from_name` varchar(255) DEFAULT '',
  `admin_email` varchar(255) DEFAULT '',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `metric_db_waits` (
  `instance_id` varchar(36) NOT NULL,
  `metric_dt` datetime NOT NULL,
  `class` varchar(45) NOT NULL,
  `total_waits` int(11) DEFAULT NULL,
  `pct_waits` decimal(4,2) DEFAULT NULL,
  `avg_wait_time` decimal(4,2) DEFAULT NULL,
  `pct_time` decimal(4,2) DEFAULT NULL,
  PRIMARY KEY (`instance_id`,`metric_dt`,`class`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `object_tags` (
  `object_id` varchar(36) NOT NULL,
  `object_type` int(11) NOT NULL,
  `tag_name` varchar(32) NOT NULL,
  PRIMARY KEY (`object_id`,`tag_name`,`object_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `poller_settings` (
  `id` int(11) NOT NULL,
  `mode_off_on` varchar(3) NOT NULL,
  `loop_delay_sec` int(11) NOT NULL,
  `max_processes` int(11) NOT NULL,
  `app_instance` varchar(1024) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `scheduler_settings` (
  `id` int(11) NOT NULL,
  `mode_off_on` varchar(3) NOT NULL,
  `loop_delay_sec` int(11) NOT NULL,
  `schedule_min_depth` int(11) NOT NULL,
  `schedule_max_days` int(11) NOT NULL,
  `clean_app_registry` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `tags` (
  `tag_name` varchar(32) NOT NULL,
  `tag_desc` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`tag_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
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
  `parameter_xml` mediumtext NOT NULL,
  PRIMARY KEY (`task_id`),
  UNIQUE KEY `IX_task_version` (`original_task_id`,`version`),
  UNIQUE KEY `IX_task_name_version` (`task_name`(64),`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `task_codeblock` (
  `task_id` varchar(36) NOT NULL DEFAULT '',
  `codeblock_name` varchar(32) NOT NULL DEFAULT '',
  PRIMARY KEY (`task_id`,`codeblock_name`),
  KEY `FK_task_codeblock_task` (`task_id`),
  CONSTRAINT `FK_task_codeblock_task` FOREIGN KEY (`task_id`) REFERENCES `task` (`task_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
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
  `cloud_id` varchar(36) DEFAULT NULL,
  `options` text,
  `schedule_id` varchar(36) DEFAULT NULL,
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
CREATE TABLE `task_instance_parameter` (
  `task_instance` bigint(20) NOT NULL,
  `parameter_xml` mediumtext NOT NULL,
  PRIMARY KEY (`task_instance`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
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
CREATE TABLE `task_step_user_settings` (
  `user_id` varchar(36) NOT NULL DEFAULT '',
  `step_id` varchar(36) NOT NULL DEFAULT '',
  `visible` int(11) NOT NULL,
  `breakpoint` int(11) NOT NULL,
  `skip` int(11) NOT NULL,
  `button` varchar(1024) DEFAULT NULL,
  PRIMARY KEY (`user_id`,`step_id`),
  KEY `FK_task_step_user_settings_task_step` (`step_id`),
  KEY `FK_task_step_user_settings_users` (`user_id`),
  CONSTRAINT `FK_task_step_user_settings_task_step` FOREIGN KEY (`step_id`) REFERENCES `task_step` (`step_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `FK_task_step_user_settings_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `user_password_history` (
  `user_id` varchar(36) NOT NULL DEFAULT '',
  `change_time` datetime NOT NULL DEFAULT '1753-01-01 00:00:00',
  `password` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`user_id`,`change_time`),
  KEY `FK_user_password_history_users` (`user_id`),
  CONSTRAINT `FK_user_password_history_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
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
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

