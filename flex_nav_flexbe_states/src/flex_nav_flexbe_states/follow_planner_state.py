#!/usr/bin/env python

###############################################################################
#  Copyright (c) 2016
#  Capable Humanitarian Robotics and Intelligent Systems Lab (CHRISLab)
#  Christopher Newport University
#
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#    1. Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#
#    3. Neither the name of the copyright holder nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
#       THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#       "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#       LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#       FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
#       COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#       INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#       BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#       LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#       CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#       LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY
#       WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#       POSSIBILITY OF SUCH DAMAGE.
###############################################################################

import actionlib
import rospy

from flexbe_core import EventState, Logger
from flexbe_core.proxy import ProxyActionClient

from flex_nav_common.msg import *
from nav_msgs.msg import Path

class FollowPlannerState(EventState):
    """
    Generates another path from a previously generated path

    -- topic        string    The topic to publish goals to

    ># plan         Path      Desired Path to follow

    <= done         Successfully reached the goal
    <= failed       Failed to generate or follow a plan
    <= preempted    The state was preempted

    """

    def __init__(self, topic):
        """
        Constructor
        """
        super(FollowPlannerState, self).__init__(outcomes=['done', 'failed', 'preempted'], input_keys=['plan'])

        self._action_topic = topic
        self._client = ProxyActionClient({self._action_topic: FollowPathAction})

    def execute(self, userdata):
        """
        Execute this state
        """

        if self._client.has_result(self._action_topic):
            result = self._client.get_result(self._action_topic)
            if result.code == 0:
                Logger.loginfo('[%s]: Planning Success!' % self.name)
                return 'done'
            elif result.code == 1:
                Logger.logerr('[%s]: Failure' % self.name)
                return 'failed'
            elif result.code == 2:
                Logger.logerr('[%s]: Preempted' % self.name)
                return 'preempted'
            else:
                Logger.logerr('[%s]: Unknown error' % self.name)
                return 'failed'


    def on_enter(self, userdata):
        """
        On enter, send action goal
        """

        result = FollowPathGoal(path = userdata.plan)

        try:
            Logger.loginfo('[%s]: Following the path to victory!' % self.name)
            self._client.send_goal(self._action_topic, result)
        except Exception as e:
            Logger.logwarn('[%s]: Failed to follow path: %s' % (self.name, str(e)))
            return 'failed'

    def on_exit(self, userdata):
        if self._action_topic in ProxyActionClient._result:
            ProxyActionClient._result[self._action_topic] = None

        if self._client.is_active(self._action_topic):
            Logger.logerr('[%s]: Canceling active goal' % self.name)
            self._client.cancel(self._action_topic)
