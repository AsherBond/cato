INSERT INTO `users` (`user_id`, `username`, `full_name`, `status`, `authentication_type`, `user_password`, `expiration_dt`, `security_question`, `security_answer`, `last_login_dt`, `failed_login_attempts`, `force_change`, `email`, `settings_xml`, `user_role`) 
	VALUES ('0002bdaf-bfd5-4b9d-82d1-fd39c2947d19','administrator','Administrator',1,'local','#ADMINPASSWORD#',NULL,NULL,NULL,NULL,0,1,'',NULL,'Administrator');
INSERT INTO `user_password_history` (`user_id`, `password`, `change_time`) 
	VALUES ('0002bdaf-bfd5-4b9d-82d1-fd39c2947d19','#ADMINPASSWORD#',now());
INSERT INTO `login_security_settings` (`id`, `pass_max_age`, `pass_max_attempts`, `pass_max_length`, `pass_min_length`, `pass_complexity`, `pass_age_warn_days`, `pass_require_initial_change`, `auto_lock_reset`, `login_message`, `auth_error_message`, `pass_history`, `page_view_logging`, `report_view_logging`, `allow_login`, `new_user_email_message`, `log_days`) 
	VALUES (1,90,99,15,6,0,5,0,5,'New Cato Install','Login Error - Please check your user id and password.',0,0,0,1,'',90);
INSERT INTO `messenger_settings` (`id`, `mode_off_on`, `loop_delay_sec`, `retry_delay_min`, `retry_max_attempts`, `smtp_server_addr`, `smtp_server_user`, `smtp_server_password`, `smtp_server_port`, `smtp_timeout`, `smtp_sl`, `from_email`, `from_name`, `admin_email`) 
	VALUES (1,'off',30,1,5,'','','',25,10,0,'user@example.com','Cloud Sidekick Messenger','');
INSERT INTO `poller_settings` (`id`, `mode_off_on`, `loop_delay_sec`, `max_processes`, `app_instance`) 
	VALUES (1,'on',3,4,'DEFAULT');
INSERT INTO `marshaller_settings` (`id`, `mode_off_on`, `loop_delay_sec`) 
	VALUES (1,'on',3);
INSERT INTO `scheduler_settings` (`id`, `mode_off_on`, `loop_delay_sec`, `schedule_min_depth`, `schedule_max_days`, `clean_app_registry`) 
	VALUES (1,'on',5,10,60,5);
