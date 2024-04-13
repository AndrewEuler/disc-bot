import os
import random
import discord
import sqlite3
from dotenv import load_dotenv
from discord.ext import commands


conn = sqlite3.connect("Discord.db")
cursor = conn.cursor()

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
hello_channel = int(os.getenv('hello_channel'))
basic_role = int(os.getenv('basic_role'))
logs_channel = int(os.getenv('logs_channel'))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(
        f'{bot.user} связан со следующей гильдией:\n'
        f'{guild.name} (id: {guild.id})\n'
    )

    for member in guild.members:  # цикл, обрабатывающий список участников

        cursor.execute(f"SELECT id FROM users where id={member.id}")  # проверка, существует ли участник в БД
        if cursor.fetchone() == None:  # Если не существует
            cursor.execute(
                f"INSERT INTO users VALUES ({member.id}, '{member.name}', 0,'[]',1,0)")  # вводит все данные об участнике в БД
        else:  # если существует
            pass
        conn.commit()  # применение изменений в БД

    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content == '@everyone':
        await message.channel.send(f'{message.author.mention}', file=discord.File('images\everyone.gif'))
    random_exp = random.randint(-30, 30)
    if random_exp > 0:
        for row in cursor.execute(f"SELECT xp,lvl,money FROM users where id={message.author.id}"):
            experience = row[0] + random_exp # к опыту добавляется количество символов
            cursor.execute(f'UPDATE users SET xp={experience} where id={message.author.id}')
            lvl_exp = experience // (row[1]*1000)
            level = row[1] + lvl_exp
            cash_now = row[2]
            cursor.execute(f'UPDATE users SET lvl={level} where id={message.author.id}')
        if lvl_exp == 1: # если уровень увеличился, то поздравить
            cash = cash_now + level * 10
            exp = experience - (level - 1) * 1000
            cursor.execute(f'UPDATE users SET xp={exp}, money={cash} where id={message.author.id}')
            await message.channel.send(f'{message.author.mention}```У тебя новый Уровень! Теперь у вас {level} lvl ```')
    elif random_exp == 0:
        await message.channel.send(f'{message.author.mention}', file=discord.File('images\exp=0.gif'))
    await bot.process_commands(message) # Далее это будет необходимо для ctx команд
    conn.commit() # применение изменений в БД


@bot.event
async def on_member_join(member):
    guild = discord.utils.get(bot.guilds, name=GUILD)
    # В какой канал будет отправляться приветствие
    channel = bot.get_channel(hello_channel)
    await channel.send(
        f'Привет {member.name}, Добро Пожаловать на наш сервер!'
    )
    role = guild.get_role(basic_role)
    if role is None:
        # Убедитесь, что роль все еще существует и является действительной.
        return
    await member.add_roles(role)

    cursor.execute(f"SELECT id FROM users where id={member.id}")  # все также, существует ли участник в БД
    if cursor.fetchone() == None:  # Если не существует
        cursor.execute(
            f"INSERT INTO users VALUES ({member.id}, '{member.name}', 10,'[]',1,0)")  # вводит все данные об участнике в БД
    else:  # Если существует
        pass
    conn.commit()  # применение изменений в БД


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('Недостаточно прав для команды.')


@bot.command(name='create-channel', help='Создает текстовый канал с указанным названием')
@commands.has_role('admin')
async def create_channel(ctx, channel_name: str):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        print(f'Creating a new channel: {channel_name}')
        await guild.create_text_channel(channel_name)
        channel = bot.get_channel(logs_channel)
        await channel.send(f'> **{ctx.author}** использовал команду - __«create-channel»__ и '
                           f'создал канал **{channel_name}**')


@bot.command(name='roll', help='Бросает 6-гранный кубик "n-раз"')
async def roll(ctx, number_of_dice: int):
    dice_of_sides = {
        1: ':one:',
        2: ':two:',
        3: ':three:',
        4: ':four:',
        5: ':five:',
        6: ':six:'
    }
    roll_dice = [dice_of_sides.get((random.choice(range(1, 7))))
                 for _ in range(number_of_dice)]
    await ctx.send('      '.join(roll_dice))
    channel = bot.get_channel(logs_channel)
    await channel.send(f'> **{ctx.author}** использовал команду - __«roll»__')


@bot.command(name='status', help='Показывает ваш статус на сервере')
async def status(ctx):
    table = [[row[0], row[1], row[2], row[3]] for row in cursor.execute(f"SELECT nickname,money,lvl,xp FROM users where id={ctx.author.id}")]
    nickname, money, lvl, xp = table[0][0], table[0][1], table[0][2], table[0][3]
    await ctx.send(f"```> Никнейм: {nickname}\n> Деньги: {money}\n> Лвл: {lvl}\n> XP: {xp} из {lvl * 1000}\n```")
    channel = bot.get_channel(logs_channel)
    await channel.send(f'> **{ctx.author}** использовал команду - __«status»__')


@bot.command(name='my-role', help='Дает тебе роль на сервере')
@commands.has_role('admin')
async def my_role(ctx, name_role: str):
    roles, guild = get_roles()
    is_role = discord.utils.get(roles, name=name_role)
    if not is_role:
        await guild.create_role(name=name_role)
        roles = get_roles()[0]
    role = list(filter(lambda x: x.name == name_role, roles))
    await ctx.author.add_roles(*role)
    channel = bot.get_channel(logs_channel)
    await channel.send(f'> **{ctx.author}** использовал команду - __«my-role»__ для получения роли **{name_role}**')


def get_roles():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    roles = guild.roles
    return roles, guild


bot.run(TOKEN, log_handler=None)