# Copyright 2012 Davoud Taghawi-Nejad
#
# Module Author: Davoud Taghawi-Nejad
#
# abcEconomics is open-source software. If you are using abcEconomics for your research you
# are requested the quote the use of this software.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License and quotation of the
# author. You may obtain a copy of the License at
#       http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from sys import getsizeof
import datetime
import json
import os
import multiprocessing
import time
from collections import defaultdict
from .online_variance import OnlineVariance
from .postprocess import to_csv
import queue
import pandas as pd


class Database:
    """Separate thread that receives data from in_sok and saves it into a
    database"""

    def __init__(self, directory, name, trade_log, plugin=None, pluginargs=[]):
        super().__init__()

        # setting up directory
        self.directory = directory
        if directory is not None:
            os.makedirs(os.path.abspath('.') + '/result/', exist_ok=True)
            if directory == 'auto':
                self.directory = (os.path.abspath('.') + '/result/' + name + '_' +
                             datetime.datetime.now().strftime("%Y-%m-%d_%H-%M"))
                """ the directory variable contains the directory of the simulation outcomes
                it can be used to generate your own graphs as all resulting
                csv files are there.
                """
            else:
                self.directory = directory
            while True:
                try:
                    os.makedirs(self.directory)
                    break
                except OSError:
                    self.directory += 'I'


        self.aggregation = defaultdict(lambda: defaultdict(OnlineVariance))
        self.round = 0

        self.plugin = plugin
        self.pluginargs = pluginargs


        self.panel_data = []
        self.write_panel_data_header = True

        if self.plugin is not None:
            self.plugin = self.plugin(*self.pluginargs)

    def put(self, msg):
        if msg[0] == 'snapshot_agg':
            _, round, group, data_to_write = msg
            if self.round == round:
                for key, value in data_to_write.items():
                    self.aggregation[group][key].update(value)
            else:
                self.make_aggregation_and_write()
                self.round = round
                for key, value in data_to_write.items():
                    self.aggregation[group][key].update(value)

        elif msg[0] == 'log':
            self.log(msg[1:])

        elif msg[0] == 'panel_log':
            (_,
              _str_round,
              group,
              _str_name,
              serial,
              data_to_write) = msg
            for action, data in data_to_write.items():
                self.log((_str_round, group, _str_name, '%s_%s' % (action, serial), data))

        elif msg[0] == 'trade_log':
            print("trade_log non implemented")

        else:
            try:
                getattr(self.plugin, msg[0])(*msg[1], **msg[2])
            except AttributeError:
                raise AttributeError(
                    "abcEconomics_db error '%s' command unknown" % msg)

    def log(self, msg):
        self.panel_data.append(msg)
        if len(self.panel_data) % 100000:
            if getsizeof(self.panel_data) > 1000000000:
                self.dump()

    def dump(self):
        if self.panel_data:
            df = pd.DataFrame(self.panel_data)
            df.rename(columns={0: 'round', 1: 'group', 2: 'name', 3: 'var', 4: 'value'}, inplace=True)

            df.pivot_table(values='value', index=['round', 'group', 'name'],
                                             columns=['var']).to_csv(self.directory + '/data.csv',
                                             mode='a', header=self.write_panel_data_header)
            self.write_panel_data_header = False
            self.panel_data = []

    def finalize(self, data):
        self.close()
        self._write_description_file(data)

    def close(self):
        self.make_aggregation_and_write()
        self.dump()

        try:
            self.plugin.close()
        except AttributeError:
            pass

    def make_aggregation_and_write(self):
        for group, table in self.aggregation.items():
            result = {'round': self.round}
            for key, data in table.items():
                result[key + '_ttl'] = data.sum()
                result[key + '_mean'] = data.mean()
                result[key + '_std'] = data.std()
                self.log((self.round, group, None, '%s_%s' % (key, '_ttl'), data.sum()))
                self.log((self.round, group, None, '%s_%s' % (key, '_mean'), data.sum()))
                self.log((self.round, group, None, '%s_%s' % (key, '_sum'), data.std()))
            self.aggregation[group].clear()

    def _write_description_file(self, data):
        if self.directory is not None:
            with open(os.path.abspath(self.directory + '/description.txt'), 'w') as description:
                description.write(json.dumps(
                    data,
                    indent=4,
                    skipkeys=True,
                    default=lambda x: 'not_serializeable'))


class MultiprocessingDatabase(Database, multiprocessing.Process):
    def __init__(self, directory, name, in_sok, trade_log, plugin=None, pluginargs=[]):
        super().__init__(directory, name, trade_log, plugin, pluginargs)
        self.in_sok = in_sok

    def run(self):
        if self.plugin is not None:
            self.plugin = self.plugin(*self.pluginargs)
        self.panel_data = []
        self.write_panel_data_header = True

        while True:
            try:
                msg = self.in_sok.get(timeout=120)
            except queue.Empty:
                print("simulation.finalize() must be specified at the end of simulation")
                msg = self.in_sok.get()
            if msg == "close":
                self.close()
                break
            self.put(msg)

    def finalize(self, data):
        self.in_sok.put('close')
        while self.is_alive():
            time.sleep(0.05)
        self._write_description_file(data)
