import os
import random
import discord
from datetime import datetime, timedelta
from discord import Option, SelectOption
import sqlite3
from dotenv import load_dotenv
from discord.ext import commands
from discord.ui import View, Select

# connect with u db (sqlite)
bd_exists = os.path.exists("Discord.db")
conn = sqlite3.connect("Discord.db")
cursor = conn.cursor()
if not bd_exists:
    cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
id INTEGER ,
nickname TEXT,
money INTEGER,
lvl INTEGER,
xp INTEGER
)
''')

# env settings
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
hello_channel = int(os.getenv('hello_channel'))
basic_role = int(os.getenv('basic_role'))
logs_channel = int(os.getenv('logs_channel'))
shop_channel = int(os.getenv('shop_channel'))
admin_role = os.getenv('admin_role')
guild_id = os.getenv('guild_id')
coupon_role = int(os.getenv('coupon_role'))
coupon_timeout = int(os.getenv('coupon_timeout'))
lvl_exp = None

# price in shop
price_role = int(os.getenv('price_role'))
price_timeout = int(os.getenv('price_timeout'))
price_case = int(os.getenv('price_case'))

# random case
list_chance = [int(i) for i in os.getenv('list_chance').split(' ')]

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)


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
                f"INSERT INTO users VALUES ({member.id}, '{member.name}', 0,1,0)")  # вводит все данные об участнике в БД
        else:  # если существует
            pass
        conn.commit()  # применение изменений в БД

    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')


@bot.event
async def on_message(message):
    global lvl_exp
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
            await message.channel.send(f'{message.author.mention}```У тебя новый Уровень! Теперь ты {level} lvl ```')
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
            f"INSERT INTO users VALUES ({member.id}, '{member.name}', 0,1,0)")  # вводит все данные об участнике в БД
    else:  # Если существует
        pass
    conn.commit()  # применение изменений в БД


# функция для режима замедления
@bot.slash_command(aliases=['сетделэй', 'сетделай'], name='setdelay', description='Устанавливает slowmode на канале',
                   guild_ids=[guild_id])
@commands.has_role(admin_role)
async def setdelay(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.respond(f"Установлен режим замедления в {seconds} сек.")
    channel = bot.get_channel(logs_channel)
    await channel.send(f'> **{ctx.author}** использовал команду - __«setdelay»__')


# функция создания текстового канала
@bot.slash_command(name='create-channel', description='Создает текстовый канал с указанным названием',
                   guild_ids=[guild_id])
@commands.has_role(admin_role)
async def create_channel(ctx, channel_name: str):
    guild = ctx.guild
    existing_channel = discord.utils.get(guild.channels, name=channel_name)
    if not existing_channel:
        print(f'Создан новый канал: {channel_name}')
        await guild.create_text_channel(channel_name)
        channel = bot.get_channel(logs_channel)
        await channel.send(f'> **{ctx.author}** использовал команду - __«create-channel»__ и '
                           f'создал канал **{channel_name}**')
        await ctx.respond(f'Создан новый канал: # {channel_name}')


# функция удаления сообщений
@bot.slash_command(name='purge', description='Очищает N-ое количество сообщений', guild_ids=[guild_id])
@commands.has_role(admin_role)
async def purge(ctx, count: int):
    await ctx.delete()
    await ctx.channel.purge(limit=count)
    channel = bot.get_channel(logs_channel)
    await channel.send(f'> **{ctx.author}** использовал команду - __«purge»__ на {count} сообщений')


# функция бросания кубиков
@bot.slash_command(name='roll', description='Бросает 6-гранный кубик "n-раз"', guild_ids=[guild_id])
async def roll(ctx, number_of_dice: Option(int, description='Число в диапазоне от 1 до 20',
                                           required=True,  min_value=1, max_value=20)):
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
    await ctx.respond('      '.join(roll_dice))
    channel = bot.get_channel(logs_channel)
    await channel.send(f'> **{ctx.author}** использовал команду - __«roll»__')


# функция для проверки статуса на сервере
@bot.slash_command(name='status', description='Показывает ваш статус на сервере', guild_ids=[guild_id])
async def status(ctx):
    table = [[row[0], row[1], row[2], row[3]] for row in cursor.execute(f"SELECT nickname,money,lvl,xp FROM users "
                                                                        f"where id={ctx.author.id}")]
    nickname, money, lvl, xp = table[0][0], table[0][1], table[0][2], table[0][3]
    await ctx.respond(f"{ctx.author.mention}```> Никнейм: {nickname}\n> Деньги: {money}\n> Лвл: {lvl}\n> XP: {xp} из {lvl * 1000}\n```")
    channel = bot.get_channel(logs_channel)
    await channel.send(f'> **{ctx.author}** использовал команду - __«status»__')


# вспомогательная функция для получения роли
async def get_roles(name_role: str):
    guild = discord.utils.get(bot.guilds, name=GUILD)
    roles = guild.roles
    is_role = discord.utils.get(roles, name=name_role)
    if not is_role:
        await guild.create_role(name=name_role)
        roles = guild.roles
    return roles


# функция выдачи роли на сервере
@bot.slash_command(name='my-role', description='Дает тебе роль на сервере', guild_ids=[guild_id])
@commands.has_any_role(admin_role, 'Купон на роль')
async def my_role(ctx, name_role: str):
    roles = await get_roles(name_role)
    role = list(filter(lambda x: x.name == name_role, roles))
    await ctx.author.add_roles(*role)
    await ctx.send(f'{ctx.author.mention} получил новую роль — **{name_role}**')
    coupon_role_list = list(filter(lambda x: x.name == 'Купон на роль', roles))
    await ctx.author.remove_roles(*coupon_role_list)
    channel = bot.get_channel(logs_channel)
    await channel.send(f'> **{ctx.author}** использовал команду - __«my-role»__ для получения роли **{name_role}**')
    await ctx.delete()


# функция отправления в таймаут юзера
@bot.slash_command(name='timeout', description='Кидает в таймаут участника', guild_ids=[guild_id])
@commands.has_any_role(admin_role, 'Купон на таймаут')
async def timeout_s(ctx, member: discord.Member, seconds: int = 0, minutes: int = 0, reason: str = None):
    duration = timedelta(seconds=seconds, minutes=minutes)
    await member.timeout(until=datetime.utcnow() + duration, reason=reason)
    await ctx.delete()
    await ctx.send(f'{ctx.author.mention} выдал таймаут {member.mention}. XD')
    roles = await get_roles('Купон на таймаут')
    coupon_timeout_list = list(filter(lambda x: x.name == 'Купон на таймаут', roles))
    await ctx.author.remove_roles(*coupon_timeout_list)
    channel = bot.get_channel(logs_channel)
    await channel.send(f'> **{ctx.author}** использовал команду - __«timeout»__ для таймаута **{member.name}**')


# вспомогательная функция для проверки баланса и его изменения
def check_balance(user_id, price, case=0):
    mon_us = cursor.execute(f"SELECT money FROM users where id={user_id}")
    money_user = [*mon_us][0][0]

    if money_user >= price:
        cash = money_user - price + case
        cursor.execute(f'UPDATE users SET money={cash} where id={user_id}')
        conn.commit()
        return True


# функция, изменяющая баланс юзера
@bot.slash_command(name='change-balance', description='Обновляет баланс у участника', guild_ids=[guild_id])
@commands.has_role(admin_role)
async def change_balance(ctx, new_balance, user_id):
    cursor.execute(f'UPDATE users SET money={new_balance} where id={user_id}')
    conn.commit()
    await ctx.delete()
    member_nickname = cursor.execute(f'SELECT nickname FROM users WHERE id IS {user_id}')
    mem = next(member_nickname)[0]
    channel = bot.get_channel(logs_channel)
    await channel.send(f'> **{ctx.author}** использовал команду - __«change-balance»__ на **{mem}**')


# выбор в магазине
async def select_callback(interaction: discord.Interaction):
    if interaction.data["values"][0] == 'Купить новую роль':
        if interaction.user.get_role(coupon_role):
            await interaction.response.send_message(f"Вы уже покупали купон на новую роль! Вы можете "
                                                    f"использовать команду «my-role»", ephemeral=True)
        else:
            if check_balance(user_id=interaction.user.id, price=price_role):
                name_role = 'Купон на роль'
                roles = await get_roles(name_role)
                role = list(filter(lambda x: x.name == name_role, roles))
                await interaction.user.add_roles(*role)
                await interaction.response.send_message(f"Вы купили купон на новую роль! Теперь вы можете "
                                                        f"использовать команду «my-role»", ephemeral=True)
            else:
                await interaction.response.send_message(f"У вас недостаточно средств в банке.", ephemeral=True)
    elif interaction.data["values"][0] == 'Замутить участника до 1 часа':
        if interaction.user.get_role(coupon_timeout):
            await interaction.response.send_message(f"Вы уже покупали купон на таймаут! Вы можете "
                                                    f"использовать команду «timeout»", ephemeral=True)
        else:
            if check_balance(user_id=interaction.user.id, price=price_timeout):
                name_role = 'Купон на таймаут'
                roles = await get_roles(name_role)
                role = list(filter(lambda x: x.name == name_role, roles))
                await interaction.user.add_roles(*role)
                await interaction.response.send_message(f"Вы купили купон на таймаут хихи! Теперь вы можете "
                                                        f"использовать команду «timeout»", ephemeral=True)
            else:
                await interaction.response.send_message(f"У вас недостаточно средств в банке.", ephemeral=True)
    elif interaction.data["values"][0] == 'Открыть кейс':
        random_prize = random.choice(list_chance)
        if check_balance(user_id=interaction.user.id, price=price_case, case=random_prize):
            await interaction.response.send_message(f"Вы открыли кейс! С него выпало {random_prize} монеток",
                                                    ephemeral=True)
        else:
            await interaction.response.send_message(f"У вас недостаточно средств в банке.", ephemeral=True)
    else:
        await interaction.response.defer()
    await interaction.message.edit(suppress=False)


# функция создания магазина
@bot.slash_command(name='create_shop', description='Создает выпадающий список магазина', guild_ids=[guild_id])
@commands.has_role(admin_role)
async def create_shop(ctx: discord.ApplicationContext):
    view = View(timeout=None)

    select = Select(
        options=[
            SelectOption(label='Выберите товар', default=True),
            SelectOption(label='Купить новую роль'),
            SelectOption(label='Замутить участника до 1 часа'),
            SelectOption(label='Открыть кейс'),
        ]
    )

    select.callback = select_callback
    view.add_item(select)
    await ctx.respond(view=view)


# обработчик ошибок функций
@setdelay.error
@create_channel.error
@purge.error
@my_role.error
@create_shop.error
@timeout_s.error
@change_balance.error
async def error_handler(ctx, error):
    if isinstance(error, commands.MissingRole) or isinstance(error, commands.MissingAnyRole):
        await ctx.delete()
        await ctx.send(f'{ctx.author.mention} недостаточно прав для команды.')
    elif isinstance(error, discord.errors.ApplicationCommandInvokeError):
        await ctx.delete()
        await ctx.send(f'{ctx.author.mention} недостаточно прав для такой команды. Вы пытаетесь посягнуть на короля!')
    else:
        raise error


bot.run(TOKEN)