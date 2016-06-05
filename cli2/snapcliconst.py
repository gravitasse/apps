#!/usr/lib/python
#
#Copyright [2016] [SnapRoute Inc]
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#       Unless required by applicable law or agreed to in writing, software
#       distributed under the License is distributed on an "AS IS" BASIS,
#       WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#       See the License for the specific language governing permissions and
#       limitations under the License.
#
# _______  __       __________   ___      _______.____    __    ____  __  .___________.  ______  __    __
# |   ____||  |     |   ____\  \ /  /     /       |\   \  /  \  /   / |  | |           | /      ||  |  |  |
# |  |__   |  |     |  |__   \  V  /     |   (----` \   \/    \/   /  |  | `---|  |----`|  ,----'|  |__|  |
# |   __|  |  |     |   __|   >   <       \   \      \            /   |  |     |  |     |  |     |   __   |
# |  |     |  `----.|  |____ /  .  \  .----)   |      \    /\    /    |  |     |  |     |  `----.|  |  |  |
# |__|     |_______||_______/__/ \__\ |_______/        \__/  \__/     |__|     |__|      \______||__|  |__|
#
#

import string

COMMAND_TYPE_DELETE = 'delete'
COMMAND_TYPE_CONFIG = 'config'
COMMAND_TYPE_SHOW = 'show'
COMMAND_TYPE_CONFIG_NOW = 'now'

# these model attribute names will possibly have the cliname changed within the cli
# model to a name picked by asicd.conf to represent a port
DYNAMIC_MODEL_ATTR_NAME_LIST = ('IntfRef', 'IfIndex', 'Port')

# lets keep track of the various two value names that might not need to be represented in the cli
CLI_COMMAND_POSITIVE_TRUTH_VALUES = ('true', 'on', 'up', '1')
CLI_COMMAND_NEGATIVE_TRUTH_VALUES = ('false', 'off', 'down', '0')

PORT_NAME_PREFIX = 'ethernet'

# helper functions
def isnumeric(v):
    return v in ('int', 'uint', 'uint8', 'int8', 'uint16', 'int16', 'uint32', 'int32')

def isboolean(v):
    return v and v.lower() in ('bool', 'boolean')

def convertStrBoolToBool(v):
    if v and str(v).lower() in ('true', '1'):
        return True
    elif v and type(v) is bool:
        return v
    return False

def convertStrNumToNum(v):
    val = v
    try:
        if isinstance(v, unicode):
            val = string.atoi(v.decode('ascii'))
        elif isinstance(v, str):
            val = string.atoi(v)
    except Exception:
        val = 0
    return val


# model macros
def GET_MODEL_COMMANDS(schemaname, model):
    return model[schemaname]["commands"]

def GET_SCHEMA_COMMANDS(schemaname, schema):
    return schema[schemaname]["properties"]["commands"]["properties"]

def getValueInSchema(schema):
    '''
    Value contains the keys for a given model object
    :param schema:
    :return:
    '''
    if "properties" in schema and \
            "value" in schema["properties"] and \
            'properties' in schema['properties']['value']:
        return schema['properties']['value']['properties']
    return None

def getValueArgumentType(attrdata):
    if 'properties' in attrdata and 'argtype' in attrdata['properties'] and 'type' in attrdata['properties']['argtype']:
        return attrdata['properties']['argtype']['type']
    return None

def getValueArgumentSelections(attrdata):
    if 'properties' in attrdata and 'argtype' in attrdata['properties'] and 'enum' in attrdata['properties']['argtype']:
        return attrdata['properties']['argtype']['enum']
    return None

def isSelectionTypeNotNeeded(selections, argtype):
    '''
    If selection is only two values and these values are represented as
    a value which is basically like enable/disable on/off... then no
    value is needed by the user, they simply just need to enter the
    attribute to set, and no attribute to unset
    :param selections:
    :param attrtype:
    :return:
    '''
    #sys.stdout.write("isSelectionTypeNeeded numsel %s isboolean %s isnumeric %s frozenset %s\n"
    #                 %(len(selections) == 2,
    #                    not isboolean(argtype),
    #                    not isnumeric(argtype),
    #                    frozenset(CLI_COMMAND_NEGATIVE_TRUTH_VALUES + CLI_COMMAND_POSITIVE_TRUTH_VALUES).intersection([str(x).lower() for x in enums])))
    return len(selections) == 2 and \
                (not isboolean(argtype) and
                    not isnumeric(argtype)
                        and len(frozenset(CLI_COMMAND_NEGATIVE_TRUTH_VALUES +
                                          CLI_COMMAND_POSITIVE_TRUTH_VALUES).intersection([str(x).lower() for x in selections])) == 2)


def getSchemaObjName(schemaname, schema):
    return schema[schemaname]['properties']['objname']['default']

def getSchemaHelp(schemaname, schema):
    return schema[schemaname]['properties']['help']['default']

def getSchemaCommandAttrDefaultArg(command):
    return command['properties']['defaultarg']['default']

def getSchemaCommandAttrIsDefaultSet(command):
    return command['properties']['isdefaultset']['default']
