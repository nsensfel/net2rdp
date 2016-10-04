#!/usr/bin/env python3
# vim:set et sw=2 ts=2 tw=80:

import argparse
import re

TINA_TRANSITION_REGEX = re.compile('tr t([0-9]+) : {(.*)} [0,w[ p([0-9]+) -> p([0-9]+)')
TINA_PLACE_W_TOKEN_REGEX = re.compile('pl p([0-9]+) : .* \(([0-9]+)\)')
TINA_PLACE_TOKEN_REGEX = re.compile('pl p([0-9]+) : .*')
TINA_NET_REGEX = re.compile('net (.*)')

CONDITION_OP = dict()
CONDITION_OP['='] = 1
CONDITION_OP['<='] = 2
CONDITION_OP['>='] = 3
CONDITION_OP['<'] = 4
CONDITION_OP['>'] = 5

CONDITION = dict()
# (ID, MIN_VALUE, MAX_VALUE)
# MIN_VALUE and MAX_VALUE are included in the acceptance range.
CONDITION['PRISE'] = (0, 0, 1)
CONDITION['LUMIERE1'] = (3, 0, 100)
CONDITION['FIN_MVMT'] = (11, 0, 1)
CONDITION['ACTION_EN_COURS'] = (12, 0, 1)
CONDITION['DERNIER_WP'] = (13, 0, 1)
CONDITION['BT_1'] = (14, 0, 1)
CONDITION['BT_2'] = (15, 0, 1)
CONDITION['BT_3'] = (16, 0, 1)
CONDITION['BT_4'] = (17, 0, 1)

ACTION = dict()
# (ID, ACCEPTS_PARAM)
ACTION['LEVER_BRAS'] = (7, False)
ACTION['BAISSER_BRAS'] = (8, False)
ACTION['BIPER'] = (11, False)
ACTION['EXIT'] = (19, False)
ACTION['INIT_NAVE'] = (20, False)
ACTION['GO_BASE'] = (22, False)
ACTION['GO_LIVRAISON'] = (23, False)
ACTION['GO_LAST_RD_WP'] = (24, False)
ACTION['GO_NEXT_WP'] = (25, False)
ACTION['ETALON_CAPT_LUMIERE'] = (26, False)
ACTION['ENVOI_BT'] = (18, True)

def parse_translation_table (tt_file):
  tt = dict()
  for line in tt_file:
    data = line.split("::")

    if (len(data) == 2): # Action
      if (data[0] in tt):
        print('[W] Multiple definitions for symbol "' + data[0] + '"')

      if (data[1] not in ACTION):
        print('[E] Unsupported action: "' + data[1] + '" in translation table.')
        exit(-1)

      (act_id, act_param) = ACTION[data[1]]

      if (act_param):
        print(
            '[E] "'
            + data[0]
            + '" uses "'
            + data[1]
            + '" without a parameter'
        )
        exit(-1)

      tt[data[0]] = ('action', act_id)

    elif (len(data) == 3): # Action with param

      if (data[0] in tt):
        print('[W] Multiple definitions for symbol "' + data[0] + '"')

      if (data[1] not in ACTION):
        print('[E] Unsupported action: "' + data[1] + '" in translation table.')
        exit(-1)

      (act_id, act_param) = ACTION[data[1]]

      if (not act_param):
        print('[E] "' + data[0] + '" uses "' + data[1] + '" with a parameter')
        exit(-1)

      tt[data[0]] = ('action', (act_id, data[2]))

    elif (len(data) == 4): # Condition
      if (data[0] in tt):
        print('[W] Multiple definitions for symbol "' + data[0] + '"')

      if (data[1] not in CONDITION):
        print(
          '[E] Unsupported condition: "'
          + data[1]
          + '" in translation table.'
        )
        exit(-1)

      (cond_id, cond_min, cond_max) = CONDITION[data[1]]

      if (not data[3].isdigit()):
        print(
          '[E] "'
          + data[0]
          + '" uses "'
          + data[3]
          + '" as if it was a positive integer.'
        )
        exit(-1)

      cond_val = int(data[3])

      if ((cond_val < cond_min) or (cond_val > cond_max)):
        print(
          '[E] Value "'
          + data[3]
          + '" in translation table entry "'
          + data[0]
          + '" is outside of the expected range (['
          + cond_min
          + ', '
          + cond_max
          + ']).'
        )
        exit(-1)

      if (data[2] not in CONDITION_OP):
        print(
          '[E] "'
          + data[0]
          + '" uses an unknown operator: "'
          + data[2]
          + '".'
        )
        exit(-1)

      tt[data[0]] = ('condition', (act_id, CONDITION_OP[data[2]], cond_val))

    else:
      print('[W] Ignored invalid Translation Table entry: "' + line + '"')

  return tt

def convert_tina_net (net_file, tt):
  name = "noname"
  first_line = "1,0"
  result = ""
  places = dict()

  for line in net_file:
    matched = TINA_NET_REGEX.search(line)

    if (matched):
      name = matched.group(1)
      continue

    matched = TINA_TRANSITION_REGEX.search(line)

    if (matched):
      continue

    matched = TINA_PLACE_W_TOKEN_REGEX.search(line)

    if (matched):
      continue

    matched = TINA_PLACE_TOKEN_REGEX.search(line)

    if (matched):
      continue

    print('[P] Program does not understand Tina NET line: "' + line + '".')
    print('[P] If this was unexpected, please inform the developer.')
    exit(-1)

  result = (
    first_line
    + result
    + '\n\r'
    + "net "
    + name
  )

  return result

parser = argparse.ArgumentParser(
  description='Converts a Tina NET file into a RDP one, using a translation table.'
)
parser.add_argument(
  'net_file',
  type=argparse.FileType(mode='r', encoding='UTF-8'),
  help='The Tinal NET file'
) # required to deal with N -> N transitions.
parser.add_argument(
  'translation_table',
  type=argparse.FileType(mode='r', encoding='UTF-8'),
  help='The translation table file'
)
parser.add_argument(
  'output_file',
  type=argparse.FileType(mode='w', encoding='UTF-8'),
  help='The output RDP file.'
)
args = parser.parse_args()

translation_table = parse_translation_table(args.translation_table)
converted_tn = convert_tina_net(args.net_file, translation_table)
print("Result:")
print(converted_tn)
