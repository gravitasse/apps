#!/usr/bin/python

import sys, getopt, socket
import jsonref
import cmdln
import readline
import rlcompleter
from optparse import OptionParser
from jsonschema import Draft4Validator
#from snap_global import Global_CmdLine
from snap_config import ConfigCmd
from commonCmdLine import CommonCmdLine, USING_READLINE
from flexswitchV2 import FlexSwitch


class CmdLine(cmdln.Cmdln, CommonCmdLine):
    """
    Help may be requested at any point in a command by entering
    a question mark '?'.  If nothing matches, the help list will
    be empty and you must backup until entering a '?' shows the
    available options.
    Two styles of help are provided:
    1. Full help is available when you are ready to enter a
       command argument (e.g. 'show ?') and describes each possible
       argument.
    2. Partial help is provided when an abbreviated argument is entered
       and you want to know what arguments match the input
       (e.g. 'show pr?'.)
    """
    # name of schema and model
    name = 'base.json'

    def __init__(self, switch_ip, model_path, schema_path):
        self.start = True
        CommonCmdLine.__init__(self, None, switch_ip, schema_path, model_path, self.name)
        cmdln.Cmdln.__init__(self)

        self.privilege = False
        self.sdk = FlexSwitch(switch_ip, 8080)

        # this loop will setup each of the cliname commands for this model level
        for subcmds, cmd in self.model["commands"].iteritems():
            # handle the links
            if 'subcmd' in subcmds:
                try:
                    for k,v in cmd.iteritems():
                        setattr(self.__class__, "do_" + self.getCliName(v), self.__getattribute__("_cmd_%s" %(k,)))
                except Exception as e:
                    sys.stdout.write("EXCEPTION RAISED on setting do_: %s\n" %(e,))
            else:
                # handle commands when are not links
                try:
                    setattr(self.__class__, "do_" + self.getCliName(self.model["commands"][subcmds]), self.__getattribute__("_cmd_%s" %(subcmds,)))
                except Exception as e:
                        sys.stdout.write("EXCEPTION RAISED on setting do_: %s\n" %(e,))


        self.setBanner(switch_ip)

    def setBanner(self, switch_ip):

        self.intro = "FlexSwitch Console Version 1.0, Connected to: " + self.switch_name
        self.intro += "\nUsing %s style cli\n" %(self.model["style"],)

    def validateSchemaAndModel(self):
        if self.model is None or self.schema is None:
            sys.exit(2)
        else:
            try:
                try:
                    self.switch_name = socket.gethostbyname(self.switch_ip)
                except socket.gaierror:
                    self.switch_name = self.switch_ip

                # update to add the prompt prefix
                self.model["prompt-prefix"] = self.switch_name

                #with open(self.modelpath, 'w') as f:
                #    jsonref.dump(self.model, f, indent=2)
                #self.setModel()
                self.setPrompt()

                # lets validate the model against the json schema
                Draft4Validator(self.model, self.schema)
            except Exception as e:
                print e
                return False
        return True

    def setPrompt(self, ):

        # set the prompt
        self.baseprompt = self.model["prompt-prefix"] + self.model["prompt"]
        self.prompt = self.model["prompt-prefix"] + self.model["prompt"]



    def cmdloop(self, intro=None):
        try:
            if self.start:
                self.start = False
                cmdln.Cmdln.cmdloop(self, intro=self.intro)
            else:
                cmdln.Cmdln.cmdloop(self, intro="")
        except KeyboardInterrupt:
            self.intro = '\n'
            self.cmdloop()


    def emptyline(self):
        pass

    @cmdln.alias("en", "ena")
    # match for schema cmd object
    def _cmd_privilege(self, arg):
        self.privilege = True
        subcmd = self.getSubCommand("privilege", self.model["commands"])
        schmacmd = self.getSubCommand("privilege", self.schema["properties"]["commands"]["properties"])
        self.prompt = self.prompt[:-1] + self.getPrompt(subcmd, schmacmd)
        self.cmdloop()


    def xdo_help(self, arg):
        doc_strings = [ (i[3:], getattr(self, i).__doc__)
            for i in dir(self) if i.startswith('do_') ]
        doc_strings = [ '  %s\t%s\n' % (i, j)
            for i, j in doc_strings if j is not None ]
        sys.stdout.write('%s\n' % ''.join(doc_strings))

    @cmdln.alias("conf t", "configure t", "configure term", "conf term", "configure terminal", "config t")
    # match for schema cmd object
    def _cmd_config(self, args):
        " Global configuration mode "

        if self.privilege is False:
            return

        functionNameAsString = sys._getframe().f_code.co_name
        name = functionNameAsString.split("_")[-1]
        pend = self.prompt[-1]
        configcmd = self.getSubCommand("config", self.model["commands"])
        schemacmd = self.getSubCommand("config", self.schema["properties"]["commands"]["properties"])
        configprompt = self.getPrompt(configcmd["config"], schemacmd["config"])
        self.prompt = self.prompt[:-1] + configprompt + pend
        cmdln.Cmdln.stop = True
        c = ConfigCmd(self, name, self.prompt, configcmd, schemacmd)
        c.cmdloop()
        # return prompt to the base of this class
        self.prompt = self.baseprompt

    def xdo_show(self, arg):
        " Show running system information "
        if "?" in self.lastcmd:
            return
        return self.commands.show_commands(arg)

    def xcomplete_show(self, text, line, begidx, endidx):
        return self.commands.auto_show(text, line, begidx, endidx)

    def do_exit(self, args):
        " Quiting FlexSwitch CLI"
        configcmd = self.getSubCommand("privilege", self.model["commands"])
        schemacmd = self.getSubCommand("privilege", self.schema["properties"]["commands"]["properties"])

        if self.prompt[-1] == self.getPrompt(configcmd, schemacmd):
            sys.stdout.write('Exiting Privilege mode\n')
            self.setPrompt()
            self.cmdloop()
        else:
            sys.stdout.write('Quiting Shell\n')
            sys.exit(0)

    def precmd(self, cmdlist):
        if len(cmdlist) > 0:
            if cmdlist[-1] == 'help':
                sys.stdout.write('%s\n' % self.__doc__)
                return ''
            elif cmdlist[-1] == '?':
                #self.command_help.show_help(line)
                return cmdlist
        return cmdlist

# *** MAIN LOOP ***
if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-s", "--switch", action="store", dest="switch_ip", type="string",
                      help="Switch IP to run the cli against", default= '127.0.0.1')
    parser.add_option("-m", "--model", action="store",type="string",
                      dest="model_path",
                      help="Path to the cli model to be used")
    parser.add_option("-j", "--jschema", action="store",type="string",
                      dest="schema_path",
                      help="Path to the cli model to be used")

    (options, args) = parser.parse_args()

    switch_ip='127.0.0.1'
    switch_ip = options.switch_ip
    model_path = options.model_path
    schema_path = options.schema_path

    cmdLine = CmdLine(switch_ip, model_path, schema_path)
    #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #result = sock.connect_ex((switch_ip,8080))
    result = True
    if result:
        cmdLine.cmdloop()
    else:
        print "FlexSwitch not reachable, Please ensure daemon is up."
        sys.exit(2)

