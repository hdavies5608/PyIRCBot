#! /usr/bin/env python

"""A simple example bot.
This is an example bot that uses the SingleServerIRCBot class from
irc.bot.  The bot enters a channel and listens for commands in
private messages and channel traffic.  Commands in channel messages
are given by prefixing the text by the bot name followed by a colon.
It also responds to DCC CHAT invitations and echos data sent in such
sessions.
The known commands are:
    stats -- Prints some channel information.
    disconnect -- Disconnect the bot.  The bot will try to reconnect
                  after 60 seconds.
    die -- Let the bot cease to exist.
    dcc -- Let the bot invite you to a DCC CHAT connection.
"""

import bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr



class TestBot(bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6697):
        bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.banned_words = open("swearWords.txt").read().splitlines()
        self.user_warnings = {}

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        nick = e.source.nick
        for i in self.banned_words:
            if i in e.arguments[0].lower():
                try:
                    self.user_warnings[nick] += 1
                except:
                    self.user_warnings[nick] = 1
                if self.user_warnings[nick] >= 3:
                    c.notice(nick, "Banned!!")
                    c.kick(self.channel, nick)
                else:
                    c.notice(nick, "Stop using banned words. Warnings: "+str(self.user_warnings[nick]))

        a = e.arguments[0].split(":", 1)
        if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
            self.do_command(e, a[1].strip())
        return

    def on_dccmsg(self, c, e):
        # non-chat DCC messages are raw bytes; decode as text
        text = e.arguments[0].decode('utf-8')
        c.privmsg("You said: " + text)

    def on_dccchat(self, c, e):
        if len(e.arguments) != 2:
            return
        args = e.arguments[1].split()
        if len(args) == 4:
            try:
                address = ip_numstr_to_quad(args[2])
                port = int(args[3])
            except ValueError:
                return
            self.dcc_connect(address, port)

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection
        arg = cmd.split(" ")[1::]
        cmd = cmd.split(" ")[0]

        if cmd == "disconnect":
            self.disconnect()
        elif cmd == "stats":
            for chname, chobj in self.channels.items():
                c.notice(nick, "--- Channel statistics ---")
                c.notice(nick, "Channel: " + chname)
                users = sorted(chobj.users())
                c.notice(nick, "Users: " + ", ".join(users))
                opers = sorted(chobj.opers())
                c.notice(nick, "Opers: " + ", ".join(opers))
                voiced = sorted(chobj.voiced())
                c.notice(nick, "Voiced: " + ", ".join(voiced))
        elif cmd == "op":
            c.privmsg("NickServ", "identify pa55word")
            c.privmsg("ChanServ", "op #dy5608 Yeti_bot")
        elif cmd == "dice":
            import random
            c.privmsg(self.channel, "Dice rolled: " + str(random.randint(1, 6)))
        elif cmd == "coin":
            import random
            outcome = "Heads" if random.randint(0, 1) == 0 else "Tails"
            c.privmsg(self.channel, "Coin was: " + outcome)
        elif cmd == "add":
            self.banned_words.extend(arg)
            print(arg)
        elif cmd == "reset":
            self.user_warnings[arg[0]] = 0
        elif cmd == "help":
            c.notice(nick, "*throws rope*")


def main():
    import sys
    if len(sys.argv) != 4:
        print("Usage: main <server[:port]> <channel> <nickname>")
        sys.exit(1)

    s = sys.argv[1].split(":", 1)
    server = s[0]
    if len(s) == 2:
        try:
            port = int(s[1])
        except ValueError:
            print("Error: Erroneous port.")
            sys.exit(1)
    else:
        port = 6697
    channel = sys.argv[2]
    nickname = sys.argv[3]

    irc_bot = TestBot(channel, nickname, server, port)
    irc_bot.start()

if __name__ == "__main__":
    main()
