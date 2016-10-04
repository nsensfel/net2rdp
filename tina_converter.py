#!/usr/bin/env python3
# vim:set et sw=2 ts=2 tw=80:
# tina_converter VERSION 2
import argparse
import re

## 'CONSTANTS' ################################################################
TINA_TRANSITION_REGEX = re.compile('tr t([0-9]+) : {(.*)} \[0,w\[ (.*) -> (.*)')
TINA_PLACE_W_TOKEN_REGEX = re.compile('pl p([0-9]+) : .* \(([0-9]+)\)')
TINA_PLACE_TOKEN_REGEX = re.compile('pl p([0-9]+) : .*')
TINA_NET_REGEX = re.compile('net (.*)')
CONDITION_OP = dict()
CONDITION_OP[''] = 0
CONDITION_OP['='] = 1
CONDITION_OP['<='] = 2
CONDITION_OP['>='] = 3
CONDITION_OP['<'] = 4
CONDITION_OP['>'] = 5

CONDITION = dict()
# (ID, MIN_VALUE, MAX_VALUE)
# MIN_VALUE and MAX_VALUE are included in the acceptance range.
CONDITION[''] = (0, 0, 0)
CONDITION['PRISE'] = (1, 0, 1)
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
ACTION[''] = (0, False)
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

## FUNCTIONS  ##################################################################

def parse_translation_table (tt_file):
  tt = dict()
  for line in tt_file:
    data = line.replace('\n','').replace('\r', '').split("::")

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

      tt[data[0]] = ('action_w_param', (act_id, data[2]))

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

      tt[data[0]] = ('condition', (cond_id, CONDITION_OP[data[2]], cond_val))

    else:
      print('[W] Ignored invalid Translation Table entry: "' + line + '"')

  return tt

def handle_link (link, pa):
  if ('*' in link):
    data = link.split('*')

    if (data[0] not in pa):
      pa[data[0]] = len(pa)

    return ('X' + str(pa[link]) + '*' + data[1])
  else:
    if (link not in pa):
      pa[link] = len(pa)

    return ('X' + str(pa[link]) + '*1')

def handle_condition (cond, tt):
  if (cond not in tt):
    print('[E] Token "' + cond + '" not defined in transition table.')
    exit(-1)

  (d_type, data) = tt[cond]

  if (d_type != 'condition'):
    print('[E] Token "' + cond + ' is incorrectly used as a condition.')
    exit(-1)

  (c_id, c_op, c_val) = data

  return (str(c_id) + ',' + str(c_op) + ',' + str(c_val))

def handle_action (act, tt):
  if (act not in tt):
    print('[E] Token "' + act + '" not defined in transition table.')
    exit(-1)

  (d_type, data) = tt[act]

  if (d_type != 'action' and d_type != 'action_w_param'):
    print('[E] Token "' + cond + ' is incorrectly used as an action.')
    exit(-1)

  if (d_type == 'action'):
    a_id = data
    a_val = 0
  else:
    (a_id, a_val) = data

  return (str(a_id) + ',' + str(a_val))

def handle_transition (transition_id, label, inputs, outputs, tt, pa):
  label = label.split('/')
  inputs = inputs.split(' ')
  outputs = outputs.split(' ')
  conditions = label[0].split(',')
  actions = label[1].split(',')

  if ('' in conditions):
    conditions.remove('')

  if ('' in actions):
    actions.remove('')

  if (len(conditions) > 4):
    print('[E] Transition "' + transition_id + '" has too many conditions.')
    exit(-1)

  if (len(actions) > 4):
    print('[E] Transition "' + transition_id + '" has too many actions.')
    exit(-1)

  result = 't' + transition_id + ':'
  result += ','.join([handle_link(input_link, pa) for input_link in inputs])

  if (len(conditions) == 0):
    result += ';?'
  else:
    result += ';' + '/'.join([handle_condition(cond, tt) for cond in conditions])

  result += ';' + ','.join([handle_link(output_link, pa) for output_link in outputs])

  if (len(actions) == 0):
    result += ';?'
  else:
    result += ';' + '/'.join([handle_action(act, tt) for act in actions])

  # We don't support priorities
  result += ';1'

  return result

def convert_tina_net (net_file, tt):
  first_line = "1,0"
  result = ""
  tokens_at = dict()
  places_aliases = dict()

  for line in net_file:
    line = line.replace('\r','').replace('\n','')

    if (line == ''):
      continue

    matched = TINA_TRANSITION_REGEX.search(line)

    if (matched):
      result += '\n' + (
        handle_transition(
          matched.group(1),
          matched.group(2),
          matched.group(3),
          matched.group(4),
          tt,
          places_aliases
        )
      )
      continue

    matched = TINA_PLACE_W_TOKEN_REGEX.search(line)

    if (matched):
      tokens_at[places_aliases['p' + matched.group(1)]] = matched.group(2)
      continue

    matched = TINA_PLACE_TOKEN_REGEX.search(line)

    if (matched):
      tokens_at[places_aliases['p' + matched.group(1)]] = '0'
      continue

    matched = TINA_NET_REGEX.search(line)

    if (matched):
      continue

    print('[P] Program does not understand Tina NET line: "' + line + '".')
    print('[P] If this was unexpected, please inform the developer.')
    exit(-1)

  first_line = (
    str(len(tokens_at) + 1)
    + ','
    + ','.join([('0' if i not in tokens_at else tokens_at[i]) for i in range(0, len(tokens_at))])
  ) + ',0'

  return (first_line + result)

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
args.output_file.write(converted_tn)
args.output_file.close()
#print("Result:")
#print(converted_tn)
