#########################################################################
# Copyright 2011 Cloud Sidekick
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#########################################################################

import os
import sys
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.mime.text import MIMEText
#from email.Utils import formatdate

base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
lib_path = os.path.join(base_path, "lib")
sys.path.insert(0, lib_path)

from catosettings import settings
from catocryptpy import catocryptpy
from catocommon import catocommon, catoprocess

class Messenger(catoprocess.CatoService):
    
    ### to do: add attachment logic into Messenger

    messenger_enabled = ""

    def get_settings(self):

        previous_mode = self.messenger_enabled

        mset = settings.settings.messenger()
        if mset:
            self.messenger_enabled = mset.Enabled
            self.loop = mset.PollLoop
#            self.min_depth = mset.Enabled
#            self.max_days = mset.Enabled
            self.retry_attempts = mset.RetryMaxAttempts
            self.smtp_server = mset.SMTPServerAddress
            self.smtp_port = mset.SMTPServerPort

            self.smtp_user = mset.SMTPUserAccount
            self.smtp_pass = mset.SMTPUserPassword

            self.smtp_from_email = mset.FromEmail
            self.smtp_from_name = mset.FromName

            if self.smtp_from_name == "":
                self.smtp_from = """\"%s\"<%s>""" % (self.smtp_from_name, self.smtp_from_email)
            else:
                self.smtp_from = self.smtp_from_email

            self.admin_email = mset.AdminEmail
            
            #output "Smtp from address is $::SMTP_FROM"
        else:
            self.logger.info("Unable to get settings - using previous values.")

        
        if previous_mode != "" and previous_mode != self.messenger_enabled:
            self.logger.info("*** Control Change: Enabled is now %s" % 
                (self.messenger_enabled))

    def update_msg_status(self, msg_id, status, err_msg):

        if status == 1:
            sql = """update message set status = 1, date_time_completed = now(), 
                    num_retries = ifnull(num_retries,0) + 1, error_message = %s where msg_id = %s"""
            self.db.exec_db(sql, (err_msg, msg_id))
        else:
            sql = """update message set status = %s, date_time_completed = now(), num_retries = 0, 
                    error_message = '' where msg_id = %s"""
            self.db.exec_db(sql, (status, msg_id))


    def check_for_emails(self):
        
        sql = """select msg_id, status, msg_to, msg_subject, msg_body, msg_cc, msg_bcc 
                from message where status in (0,1) and ifnull(num_retries,0) <= %s 
                order by msg_id asc"""
        rows = self.db.select_all(sql, (self.retry_attempts))
        if rows:
            self.logger.info("Processing %d messages...", (len(rows)))
            try: 
                server = smtplib.SMTP_SSL(self.smtp_server, int(self.smtp_port))
                server.login(self.smtp_user, self.smtp_pass)
            except Exception, e:
                for row in rows:
                    msg_id = row[0]
                    err_msg = str(e)
                    self.update_msg_status(msg_id, 1, err_msg)

            for row in rows:
                msg_id = row[0]
                status = row[1]
                msg_to = row[2]
                msg_subject = row[3]
                msg_body = row[4]
                msg_cc = row[5]
                msg_bcc = row[6]

                msg = MIMEMultipart('alternative')
                msg["To"] = msg_to
                msg["From"] = self.smtp_from
                msg["Subject"] = msg_subject
                #msg["Date"] = formatdate(localtime=True)
                part1 = MIMEText(msg_body, 'plain')
                part2 = MIMEText(msg_body, 'html')
                msg.attach(part1)
                msg.attach(part2)
                try:
                    server.sendmail(self.smtp_from, msg_to, msg.as_string())
                except Exception, e:
                    err_msg = str(e)
                    self.update_msg_status(msg_id, 1, err_msg)
                else:
                    self.update_msg_status(msg_id, 2, "")
                del(msg)

            server.quit()


    def main_process(self):
        """main process loop, parent class will call this"""
        self.check_for_emails()


