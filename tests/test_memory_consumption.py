# Copyright 2018 Davide Spadini
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

import os
import psutil
import json
import sys
if 'TRAVIS' in os.environ:
    import requests
    webhook_url = os.environ['WEBHOOK_URL']
from pydriller.repository_mining import RepositoryMining
from datetime import datetime


def test_memory():
    if 'TRAVIS' not in os.environ:
        return

    diff_with_nothing, all_commits_with_nothing = mine(0)
    diff_with_everything, all_commits_with_everything = mine(1)
    diff_with_metrics, all_commits_with_metrics = mine(2)

    logs_and_post_on_slack(diff_with_nothing, all_commits_with_nothing,
                           diff_with_everything, all_commits_with_everything,
                           diff_with_metrics, all_commits_with_metrics)

    assert 1240 == len(all_commits_with_nothing) == len(all_commits_with_everything) == len(all_commits_with_metrics)


def logs_and_post_on_slack(diff_with_nothing, all_commits_with_nothing,
                           diff_with_everything, all_commits_with_everything,
                           diff_with_metrics, all_commits_with_metrics):

    text = "*PYTHON V{}.{}*\n" \
           "*Max memory (MB)*\n" \
           "With nothing: {}, with everything: {}, with metrics: {}\n" \
           "*Min memory (MB)*\n" \
           "With nothing: {}, with everything: {}, with metrics: {} \n" \
           "*Time*\n" \
           "With nothing: {}:{}:{}, with everything: {}:{}:{}, with metrics: {}:{}:{} \n" \
           "*Total number of commits*: {}\n" \
           "*Commits per second:*\n" \
            "With nothing: {}, with everything: {}, with metrics: {}"

    slack_data = {
        'text': text.format(
                sys.version_info[0], sys.version_info[1],
                max(all_commits_with_nothing), max(all_commits_with_everything), max(all_commits_with_metrics),
                min(all_commits_with_nothing), min(all_commits_with_everything), min(all_commits_with_metrics),
                diff_with_nothing.seconds // 3600, (diff_with_nothing.seconds % 3600) // 60, diff_with_nothing.seconds % 60,
                diff_with_everything.seconds // 3600, (diff_with_everything.seconds % 3600) // 60, diff_with_everything.seconds % 60,
                diff_with_metrics.seconds // 3600, (diff_with_metrics.seconds % 3600) // 60, diff_with_metrics.seconds % 60,
                len(all_commits_with_nothing),
                len(all_commits_with_nothing) / diff_with_nothing.seconds,
                len(all_commits_with_everything) / diff_with_everything.seconds,
                len(all_commits_with_metrics) / diff_with_metrics.seconds
        )}
    requests.post(
        webhook_url, data=json.dumps(slack_data),
        headers={'Content-Type': 'application/json'}
    )


def mine(_type):
    p = psutil.Process(os.getpid())
    dt1 = datetime(2017, 1, 1)
    dt2 = datetime(2017, 7, 1)
    all_commits = []

    start = datetime.now()
    for commit in RepositoryMining('test-repos/hadoop',
                                   since=dt1,
                                   to=dt2).traverse_commits():
        memory = p.memory_info()[0] / (2 ** 20)
        all_commits.append(memory)

        h = commit.author.name

        if _type == 0:
            continue

        for mod in commit.modifications:
            dd = mod.diff

            if _type == 1:
                continue

            if mod.filename.endswith('.java'):
                cc = mod.complexity

    end = datetime.now()

    diff = end - start

    return diff, all_commits
