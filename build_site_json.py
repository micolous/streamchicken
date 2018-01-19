#!/usr/bin/env python
"""
build_site_json.py - Builds streaming site schedule JSON.

Copyright 2018 Michael Farrell <micolous+git@gmail.com>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

from argparse import ArgumentParser, FileType
from datetime import datetime, timedelta
from json import load, dump
from isodate import parse_datetime, parse_duration
from pytz import timezone


def build_site_json(schedule_f, rooms_f, output_f):
  schedule = load(schedule_f)
  rooms = load(rooms_f)
  unknown_rooms = set()
  local_tz = timezone(rooms['tz'])
  
  rooms_entries = {}
  for room in rooms['rooms']:
    rooms_entries[room['id']] = room
    room['events'] = []
  
  for event in schedule:
    location = event['location_slug']
    
    if location not in rooms_entries.keys():
      unknown_rooms.add(location)
      continue

    start = local_tz.localize(parse_datetime(event['start']))
    duration_segs = event['duration'].split(':')
    duration = timedelta(hours=int(duration_segs[0]), minutes=int(duration_segs[1]))
    if len(duration_segs) == 3:
      duration += timedelta(seconds=int(duration_segs[2]))
    end = start + duration

    output_event = {
      'uid': event['conf_key'],  # unique ID
      'sta': start.isoformat(),  # start
      'end': end.isoformat(),    # end
      'nam': event['name'],      # name / title
    }
    
    if event['authors'] != '':
      output_event['aut'] = event['authors']  # authors
    
    if event['conf_url'] != '':
      output_event['abs'] = event['conf_url'] # abstract url
    
    rooms_entries[location]['events'].append(output_event)

  for room in rooms_entries.itervalues():
    room['events'].sort(key=lambda o: o['sta'])
  
  output = {
    'ts': local_tz.localize(datetime.now()).isoformat(),
    'rooms': rooms['rooms'],
  }
  
  if unknown_rooms:
    print 'Found %d unknown rooms' % (len(unknown_rooms),)
    for unknown_room in unknown_rooms:
      print repr(unknown_room),

  dump(output, output_f)


def main():
  parser = ArgumentParser()
  parser.add_argument('-s', '--schedule', required=True, type=FileType('rb'))
  parser.add_argument('-r', '--rooms', required=True, type=FileType('rb'))
  parser.add_argument('-o', '--output', required=True, type=FileType('wb'))

  options = parser.parse_args()

  build_site_json(options.schedule, options.rooms, options.output)

if __name__ == '__main__':
  main()
