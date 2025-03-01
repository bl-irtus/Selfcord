import asyncio
from selfcord.api import gateway, http
import inspect
from selfcord.models import Client, TextChannel, GroupChannel, DMChannel, VoiceChannel, Guild
from collections import defaultdict
from aioconsole import aprint
import time
from selfcord.utils import Command, CommandCollection, Context





class Bot:
    def __init__(self, show_beat: bool=False, prefixes: list=["s!"]) -> None:
        self.show_beat = show_beat
        self.token = None
        self.http = http()
        self.t1 = time.perf_counter()
        self.gateway = gateway(self.http, self.show_beat)
        self._events = defaultdict(list)
        self.commands = CommandCollection(self)
        self.prefixes = prefixes if isinstance(prefixes, list) else [prefixes]


    def run(self, token: str):
        """Used to start connection to gateway as well as gather user information

        Args:
            token (str): _description_
        """
        self.token = token
        async def runner():
            data = await self.http.static_login(token)
            self.user: Client = Client(data) # type: ignore
            await self.gateway.start(token, self.user, self)
        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            pass

    @property
    def latency(self):
        "Latency of heartbeat ack, gateway latency essentially"
        return self.gateway.latency

    # For events
    async def _help(self):
        """I call this on bot initialisation, it's the inbuilt help command
        """
        @self.cmd("The help command!", aliases=["test"])
        async def help(ctx):
            await ctx.message.delete()
            msg = f"```diff\n"
            msg += f"+ {self.user} selfbot\n+ Prefixes:   {self.prefixes}\n\n"
            msg += f"- Commands\n"
            for command in self.commands:
                msg += f"- {command.name}:    {command.description}\n"
            msg += f"```"
            await ctx.send(f"{msg}")


    def on(self, event: str):
        """Decorator for events

        Args:
            event (str): The event to check for
        """
        def decorator(coro):
            if not inspect.iscoroutinefunction(coro):
                raise RuntimeWarning("Faulure")
            else:
                self._events[event].append(coro)
                def wrapper(*args, **kwargs):
                    result = self._events[event].append(coro)
                    return result
                return wrapper
        return decorator

    async def emit(self, event, *args, **kwargs):
        """Used to essentially push values to the decorator

        Args:
            event (str): The event name
        """
        on_event = "on_{}".format(event)
        try:
            if hasattr(self, on_event):
                await getattr(self, on_event)(*args, **kwargs)
            if event in self._events:
                for callback in self._events[event]:
                    asyncio.create_task(callback(*args, **kwargs))
        except Exception as e:
            await aprint(e)

    def cmd(self, description="", aliases=[]):
        """Decorator to add commands for the bot

        Args:
            description (str, optional): Description of command. Defaults to "".
            aliases (list, optional): Alternative names for command. Defaults to [].

        Raises:
            RuntimeWarning: If you suck and don't use a coroutine
        """
        if isinstance(aliases, str):
            aliases = [aliases]

        def decorator(coro):
            name = coro.__name__
            if not inspect.iscoroutinefunction(coro):
                raise RuntimeWarning("Faulure")
            else:
                cmd = Command(name=name, description=description, aliases=aliases, func=coro)
                self.commands.add(cmd)
            return cmd
        return decorator



    async def process_commands(self, msg):
        """What is called in order to actually get command input and run commands

        Args:
            msg (str): The message containing command
        """
        context = Context(self, msg, self.http)
        await context.invoke()


    def get_channel(self, channel_id: str):
        """Function to help retrieve channel from bot cache

        Args:
            channel_id (str): The channel id to search for

        Returns:
            Channel: The Channel object
        """
        for channel in self.user.private_channels:
            if channel_id == channel.id:
                return channel
        for guild in self.user.guilds:
            for channel in guild.channels:
                if channel_id == channel.id:
                    return channel




    def get_guild(self, guild_id: str):
        """Function to help retrieve guild from bot cache

        Args:
            guild_id (str): The guild id to search for

        Returns:
            Guild: The Guild object
        """
        for guild in self.user.guilds:
            if guild.id == guild_id:
                return guild





