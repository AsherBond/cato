#########################################################################
# Copyright 2014 Cloud Sidekick
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

# requires croniter from https://github.com/taichino/croniter
from croniter import croniter
from datetime import datetime

def get_cron(start_dt, now, months, days_or_weeks, days, hours, minutes):

    if not start_dt:
        # this means we are not selecting a start date in the future
        # the schedule should start now
        start_dt = now
    else:
        # start at the start date plus one second
        # why? I don't recall
        start_dt = start_dt + 1

    if days_or_weeks == 1:
        # this will be days of the week, 0 - 6
        # 0 = sunday, 1 = monday, ... 6 = saturday
        dow = days
        dom = "*"
    else:
        # this will be days of the month, 1 - 31
        dow = "*"

        # the following is because days stored in the database start at 0 and end at 30
        # we need to translate to cron style by adding a 1
        dom = ",".join([str((int(i) + 1)) for i in days.split(",")])

    # the following is because months stored in the database start at 0 and end at 11
    # we need to translate to cron style by adding a 1
    months = ",".join([str((int(i) + 1)) for i in months.split(",")])

    # translate the database date time to a python datetime object
    the_start_dt = datetime.fromtimestamp(start_dt)

    # piece together the date into a cron-style string
    # see http://en.wikipedia.org/wiki/Cron#Predefined_scheduling_definitions
    cron_string = minutes + " " + hours + " " + dom + " " + months + " " + dow

    # use croniter library to setup an interator of datetimes
    citer = croniter(cron_string, the_start_dt)
    return citer
