#    ___      _       _     ____   ___ _____ 
#   / _ \ ___(_)_ __ | |_  | __ ) / _ \_   _|
#  | | | / __| | '_ \| __| |  _ \| | | || |  
#  | |_| \__ \ | | | | |_  | |_) | |_| || |  
#  \___/|___/_|_| |_|\__| |____/ \___/ |_|  

# Made by kowa, by <3

import json
import requests
import discord
import asyncio
import os
import base64
import pyfiglet
import aiohttp
import shodan
import random
import re
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from discord.ext import commands, tasks

with open('config.json') as config_file:
    config = json.load(config_file)
    TOKEN = config['token']
    HUNTER_API_KEY = config['hunter_api_key']

intents = discord.Intents.default()
# intents.message_content = True
intents.guilds = True
intents.members = True
intents.messages = True
intents.reactions = True 
intents.presences = True  

special_members = {
    1176828617334997122,
    1146464575085097153,
    775872956529901608,
    1220828608298487891
}

bot = commands.Bot(command_prefix='>', intents=intents, help_command=None)
SHODAN_API_KEY = ' iwZQcDGSjLedGfraH8IId4Qr9pUBleab'
shodan_api = shodan.Shodan(SHODAN_API_KEY)
TARGET_CHANNEL_ID = 1274717816939085855
mogged_users = {}

ascii_art = """\033[35m
 _   _   ____   ___ _____ 
| \\ | | | __ ) / _ \\_   _|
|  \\| | |  _ \\| | | || |  
| |\\  | | |_) | |_| || |  
|_| \\_| |____/ \\___/ |_|  
\033[0m"""

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


API_URL = 'http://satanservices.xyz:1337/api/attack'
USERNAME = 'dedsec'
KEY = 'kirahttps2'
invite_tracker = {}

load_dotenv()
DISCORD_TOKENS = json.loads(os.getenv("DISCORD_TOKENS", "[]"))

anti_raid_enabled = False
message_counts = {}
message_limit = 5 
time_frame = 5  

leet_mapping = {
    'a': ['@', '4'],
    'e': ['3'],
    'l': ['1'],
    'o': ['0'],
    't': ['7'],
    's': ['5', '$'],
    'i': ['1', '!'],
    'b': ['8']
}

authorized_users = [
    1253372690975428651,  
    1268299911347044426,
    498085260244811786,
    689172217551913014,
    1269817146481971230
]

def to_leet_speak(text):
    """Convertit le texte en 'leet speak' en remplaçant certaines lettres."""
    result = ""
    for char in text:
        if char.lower() in leet_mapping and random.random() > 0.5:
            result += random.choice(leet_mapping[char.lower()])
        else:
            result += char
    return result

async def check_authorization(ctx):
    """Vérifie si l'utilisateur qui exécute la commande est autorisé."""
    if ctx.author.id not in authorized_users:
        await ctx.send("Vous n'êtes pas autorisé à utiliser cette commande.")
        return False
    return True

def load_linked_accounts():
    try:
        with open('linked_accounts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_linked_accounts(linked_accounts):
    with open('linked_accounts.json', 'w') as f:
        json.dump(linked_accounts, f, indent=4)

linked_accounts = load_linked_accounts()

@tasks.loop(seconds=1)
async def change_status():
    bio_list = [
        "Join",
        "discord.gg/nrevolution"
    ]
    for bio in bio_list:
        await bot.change_presence(activity=discord.Game(name=bio))
        await asyncio.sleep(0.5)

@bot.event
async def on_ready():
    for guild in bot.guilds:
        invites = await guild.invites()
        invite_tracker[guild.id] = invites

@bot.event
async def on_ready():
    guild = bot.guilds[0]
    existing_channel = discord.utils.get(guild.channels, name="message-scraper")
    if existing_channel is None:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            discord.utils.get(guild.roles, name="Staff"): discord.PermissionOverwrite(read_messages=True)
        }
        await guild.create_text_channel('message-scraper', overwrites=overwrites)
    
    print(f'{bot.user.name} est connecté et prêt à scraper les messages.')


@bot.event
async def on_guild_channel_delete(channel):
    if channel.guild:
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if entry.user.id not in authorized_users:
                new_channel = await channel.guild.create_text_channel(name=channel.name)
                
                await remove_user_permissions(entry.user, channel.guild)
                break

async def remove_user_permissions(user, guild):
    """Retire toutes les permissions d'un utilisateur sur le serveur."""
    for role in guild.roles:
        if role.name != "@everyone":
            try:
                await user.remove_roles(role)
            except discord.Forbidden:
                print(f"Impossible de retirer le rôle {role.name} de l'utilisateur {user.name}.")
            except discord.HTTPException as e:
                print(f"Erreur HTTP en retirant le rôle {role.name} de l'utilisateur {user.name}: {e}")

    if user.bot and user.id not in authorized_users:
        for role in user.roles:
            try:
                await user.remove_roles(role)
            except discord.Forbidden:
                print(f"Impossible de retirer le rôle {role.name} de l'utilisateur {user.name}.")
            except discord.HTTPException as e:
                print(f"Erreur HTTP en retirant le rôle {role.name} de l'utilisateur {user.name}: {e}")


@bot.event
async def on_member_join(member):
    now = datetime.now(timezone.utc)
    account_age = (now - member.created_at).days

    if account_age < 20:
        alert_channel_id = 1275166848123666524
        alert_channel = bot.get_channel(alert_channel_id)

        if alert_channel:
            embed = discord.Embed(
                title="COMPTE SUSPICIEUX !",
                description=f"Le compte {member.mention} vient de débarquer sur le serveur, il a été créé il y a moins de 20 jours.",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Compte créé le {member.created_at.strftime('%d %B %Y à %H:%M UTC')}")
            embed.timestamp = now

            await alert_channel.send(embed=embed)
    invites_before = invite_tracker.get(member.guild.id, [])
    invites_after = await member.guild.invites()
    inviter = None
    for invite in invites_before:
        found_invite = discord.utils.find(lambda inv: inv.code == invite.code, invites_after)
        if found_invite and invite.uses < found_invite.uses:
            inviter = invite.inviter
            break
    invite_tracker[member.guild.id] = invites_after

    welcome_channel_id = 1273309023663296572
    rules_channel_id = 1270011554364129353
    welcome_channel = bot.get_channel(welcome_channel_id)

    if welcome_channel:
        if inviter:
            await welcome_channel.send(f"Bienvenue <@{member.id}>, n'hésite pas à lire le règlement dans <#{rules_channel_id}> **(Invité par {inviter.mention})**")
        else:
            await welcome_channel.send(f"Bienvenue <@{member.id}>, n'hésite pas à lire le règlement dans <#{rules_channel_id}>")

    if member.id in special_members:
        staff_channel_id = 1275166848123666524
        staff_channel = bot.get_channel(staff_channel_id)

        if staff_channel:
            embed = discord.Embed(
                title="STAFF SERENADE !",
                description=f"Le membre {member.mention} ({member.name}) a rejoint le serveur.",
                color=discord.Color.blue()
            )
            await staff_channel.send(embed=embed)

@bot.event
async def on_invite_create(invite):
    invites = await invite.guild.invites()
    invite_tracker[invite.guild.id] = invites

@bot.event
async def on_invite_delete(invite):
    invites = await invite.guild.invites()
    invite_tracker[invite.guild.id] = invites

@bot.event
async def on_message(message):
    if not message.author.bot:
        try:
            with open("messages.txt", "a", encoding="utf-8") as file:
                file.write(f"{message.author.display_name}, {message.author.id}, {message.content}\n")
        except Exception as e:
            print(f"Erreur lors de l'écriture dans le fichier : {e}")

        target_channel = bot.get_channel(TARGET_CHANNEL_ID)
        if target_channel:
            try:
                await target_channel.send(f"{message.author.display_name} ({message.author.id}): {message.content}")
            except Exception as e:
                print(f"Erreur lors de l'envoi du message au salon cible : {e}")

        await bot.process_commands(message)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    now = datetime.now()
    if message.author.id not in message_counts:
        message_counts[message.author.id] = []
    message_counts[message.author.id] = [timestamp for timestamp in message_counts[message.author.id] if now - timestamp < timedelta(seconds=time_frame)]
    message_counts[message.author.id].append(now)
    if len(message_counts[message.author.id]) > message_limit and antiraid_enabled:
        try:
            await message.author.send("Vous avez été expulsé pour avoir spammé.")
            await message.guild.kick(message.author, reason="Anti-raid : Spam détecté")
            print(f"Kicked {message.author} for spamming.")
        except discord.Forbidden:
            print("Le bot n'a pas les permissions nécessaires pour kicker l'utilisateur.")
        except Exception as e:
            print(f"Une erreur s'est produite : {e}")
    await bot.process_commands(message)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.author.id in mogged_users:
        mode = mogged_users[message.author.id]
        if mode == "girl":
            response = f"{message.content} :nail_care:"
            await message.reply(response)
        elif mode == "haxor":
            response = to_leet_speak(message.content)
            await message.reply(response)

    await bot.process_commands(message)

@bot.event
async def on_ready():
    clear_console()
    server_names = ', '.join([guild.name for guild in bot.guilds]) 
    user_name = bot.user.name

    print(ascii_art)
    print(f"~ Nom du bot: {user_name}")
    print(f"~ Serveur(s) connecté(s): {server_names}")
    print(f"~ Nombre de membres: {sum(guild.member_count for guild in bot.guilds)}")

    change_status.start()

class Ascii(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ascii', help='Transformez votre texte en caractères ascii ! (moins de 20 caractères)')
    async def ascii(self, ctx, *, text: str):
        if len(text) > 20:
            await ctx.send("Veuillez préciser un texte valide (moins de 20 caractères) !")
            return
        rendered = pyfiglet.figlet_format(text)
        await ctx.send(f"```{rendered}```")

def setup(bot):
    bot.add_cog(Ascii(bot))

@bot.event
async def on_message(message):
    if anti_raid_enabled and not message.author.bot:
        link_patterns = [
            r'https://',
            r'http://',
            r'discord\.gg/',
            r'\bdiscord\.gg\b',
            r'\.gg/',
            r'/serenade'
        ]
        
        if any(re.search(pattern, message.content, re.IGNORECASE) for pattern in link_patterns):
            await message.delete()
            await message.channel.send("Les liens sont interdits !")
        else:
            await bot.process_commands(message)
    else:
        await bot.process_commands(message)

@bot.command()
async def mog(ctx, member: discord.Member, mode: str):
    if not await check_authorization(ctx):
        return

    if mode.lower() in ["girl", "haxor"]:
        mogged_users[member.id] = mode.lower()
        await ctx.send(f"{member.mention} a été mogé en mode '{mode}'.")
    else:
        await ctx.send(f"Mode '{mode}' non reconnu. Les modes disponibles sont : 'girl', 'haxor'.")

@bot.command()
async def antiraid(ctx, state: str):
    global anti_raid_enabled
    if ctx.author.guild_permissions.administrator:
        if state.lower() == 'on':
            anti_raid_enabled = True
            await ctx.send("Anti-raid activé.")
        elif state.lower() == 'off':
            anti_raid_enabled = False
            await ctx.send("Anti-raid désactivé.")
        else:
            await ctx.send("Utilisation : >antiraid <on/off>")
    else:
        await ctx.send("Vous n'avez pas les permissions nécessaires pour exécuter cette commande.")

@bot.command()
async def lookup(ctx, user_id: int):
    """Affiche les serveurs en commun et les amis en commun entre les comptes liés et l'utilisateur spécifié."""
    if user_id not in linked_accounts:
        await ctx.send("L'utilisateur spécifié n'est pas lié au bot.")
        return
    
    user_data = linked_accounts[user_id]
    if 'servers' not in user_data or 'friends' not in user_data:
        await ctx.send("Les informations de l'utilisateur ne sont pas complètement liées.")
        return

    # Récupérer les serveurs de l'utilisateur spécifié
    target_user = bot.get_user(user_id)
    if target_user is None:
        await ctx.send("Utilisateur non trouvé.")
        return
    
    target_guilds = [guild.id for guild in bot.guilds if target_user in guild.members]
    target_friends = [friend.id for friend in target_user.friends]

    # Vérifier les serveurs en commun
    common_servers = []
    for guild in bot.guilds:
        if guild.id in target_guilds:
            common_servers.append(guild.name)

    # Vérifier les amis en commun
    common_friends = [friend for friend in target_user.friends if friend.id in user_data['friends']]

    # Formatage du message
    response = f"**Serveurs en commun:**\n{', '.join(common_servers) if common_servers else 'Aucun serveur en commun.'}\n\n"
    response += f"**Amis en commun:**\n{', '.join(f"{friend.name}#{friend.discriminator}" for friend in common_friends) if common_friends else 'Aucun ami en commun.'}"

    await ctx.send(response)

@bot.command()
async def demog(ctx, member: discord.Member):
    if not await check_authorization(ctx):
        return

    if member.id in mogged_users:
        del mogged_users[member.id]
        await ctx.send(f"{member.mention} a été démogé.")
    else:
        await ctx.send(f"{member.mention} n'était pas mogé.")

# @bot.command()
# async def searchmess(ctx, user_id: int):
#     try:
#         with open("messages.txt", "r", encoding="utf-8") as file:
#             lines = file.readlines()
        
#         user_messages = [line for line in lines if line.split(", ")[1] == str(user_id)]

#         if user_messages:
#             output_file = f"{user_id}_messages.txt"
#             with open(output_file, "w", encoding="utf-8") as file:
#                 file.writelines(user_messages)
            
#             await ctx.send(file=discord.File(output_file))
            
#             os.remove(output_file)
#         else:
#             await ctx.send("Aucun message trouvé pour cet utilisateur.")
#     except Exception as e:
#         await ctx.send(f"Une erreur s'est produite : {e}")

@bot.command()
async def ascii(ctx, *, text: str):
    try:
        if len(text) > 20:
            await ctx.send("Veuillez préciser un texte valide (moins de 20 caractères) !")
            return
        rendered = pyfiglet.figlet_format(text)
        await ctx.send(f"```{rendered}```")
        
    except Exception as e:
        await ctx.send(f"Une erreur s'est produite : {e}")

@bot.command()
async def wl(ctx, member: discord.Member):
    """Ajoute un utilisateur à la liste des utilisateurs autorisés."""
    if not await check_authorization(ctx):
        return
    
    if member.id in authorized_users:
        await ctx.send(f"{member.mention} est déjà autorisé.")
    else:
        authorized_users.append(member.id)
        await ctx.send(f"{member.mention} a été ajouté à la liste des utilisateurs autorisés.")

@bot.command()
async def unwl(ctx, member: discord.Member):
    """Retire un utilisateur de la liste des utilisateurs autorisés."""
    if not await check_authorization(ctx):
        return
    
    if member.id in authorized_users:
        authorized_users.remove(member.id)
        await ctx.send(f"{member.mention} a été retiré de la liste des utilisateurs autorisés.")
    else:
        await ctx.send(f"{member.mention} n'est pas dans la liste des utilisateurs autorisés.")

@bot.command()
async def wllist(ctx):
    """Affiche la liste des utilisateurs autorisés."""
    if not await check_authorization(ctx):
        return
    
    if authorized_users:
        user_list = "\n".join([f"<@{user_id}>" for user_id in authorized_users])
        embed = discord.Embed(
            title="Liste des utilisateurs autorisés",
            description=user_list,
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("Aucun utilisateur n'est autorisé.")


@bot.command()
async def search(ctx, *, query: str):
    api_url = f"https://osint.lolarchiver.com/database_lookup?q={query}&exact=false"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.headers.get('Content-Type') == 'application/json':
                    data = await response.json()
                    
                    if data:
                        content = ""
                        for key, value in data.items():
                            content += f"{key}: {value}\n"
                        
                        file_path = "search_results.txt"
                        with open(file_path, "w", encoding="utf-8") as file:
                            file.write(content)
                        
                        await ctx.send(file=discord.File(file_path))
                        os.remove(file_path)
                    else:
                        await ctx.send("Aucun résultat trouvé pour cette recherche.")
                else:
                    text = await response.text()
                    await ctx.send(f"Erreur lors de la recherche. Réponse inattendue :\n{text}")

    except Exception as e:
        await ctx.send(f"Un problème est survenu. Veuillez réessayer dans quelques secondes.\nErreur : {str(e)}")



@bot.command()
async def iplookup(ctx, ip_address: str):
    try:
        url = f'http://ipwho.is/{ip_address}'
        response = requests.get(url)

        if response.status_code != 200:
            await ctx.send(f"Erreur lors de la récupération des informations pour l'IP: {ip_address}\nStatut de la réponse: {response.status_code}")
            return
        
        data = response.json()

        if not data.get('success', False):
            await ctx.send(f"Impossible de récupérer des informations pour l'IP: {ip_address}")
            return

        embed = discord.Embed(title=f"Informations pour l'IP: {ip_address}", color=discord.Color.purple())
        embed.add_field(name="🌐 IP", value=data.get('ip', 'Inconnu'), inline=False)
        embed.add_field(name="✅ Succès", value=data.get('success', 'Inconnu'), inline=False)
        embed.add_field(name="🔢 Type", value=data.get('type', 'Inconnu'), inline=False)
        embed.add_field(name="🌍 Continent", value=data.get('continent', 'Inconnu'), inline=False)
        embed.add_field(name="🌍 Code du continent", value=data.get('continent_code', 'Inconnu'), inline=False)
        embed.add_field(name="🇨🇭 Pays", value=data.get('country', 'Inconnu'), inline=False)
        embed.add_field(name="🇨🇭 Code du pays", value=data.get('country_code', 'Inconnu'), inline=False)
        embed.add_field(name="🏙️ Région", value=data.get('region', 'Inconnu'), inline=False)
        embed.add_field(name="🏙️ Code de la région", value=data.get('region_code', 'Inconnu'), inline=False)
        embed.add_field(name="🌆 Ville", value=data.get('city', 'Inconnu'), inline=False)
        embed.add_field(name="📍 Latitude", value=data.get('latitude', 'Inconnu'), inline=False)
        embed.add_field(name="📍 Longitude", value=data.get('longitude', 'Inconnu'), inline=False)
        embed.add_field(name="📮 Code postal", value=data.get('postal', 'Inconnu'), inline=False)
        embed.add_field(name="ASN", value=data.get('connection', {}).get('asn', 'Inconnu'), inline=False)
        embed.add_field(name="Organisation", value=data.get('connection', {}).get('org', 'Inconnu'), inline=False)
        embed.add_field(name="ISP", value=data.get('connection', {}).get('isp', 'Inconnu'), inline=False)
        embed.add_field(name="Domaine", value=data.get('connection', {}).get('domain', 'Inconnu'), inline=False)
        embed.set_footer(text=f"👤 Sent by: {ctx.author.display_name}")

        await ctx.send(embed=embed)

    except requests.exceptions.RequestException as e:
        await ctx.send(f"Erreur lors de la récupération des informations pour l'IP: {ip_address}\nErreur: {e}")


@bot.command()
async def ping(ctx):
    latency = bot.latency * 1000  
    guild = ctx.guild
    member_count = guild.member_count
    response = (
        f'Pong!\n'
        f'Latence: {latency:.2f} ms\n'
        f'Serveur: {guild.name}\n'
        f'Nombre de membres: {member_count}\n'
        f'Utilisateur: {ctx.author.display_name}'
    )
    await ctx.send(response)

@bot.command()
async def numinfo(ctx, phone_number: str):
    try:
        url = f'https://api.numlookupapi.com/v1/validate/{phone_number}?apikey=num_live_KAYJ5wGhBzC92t3glm9kcjYXAYCWLsk51r0ICECM'
        response = requests.get(url)

        if response.status_code != 200:
            await ctx.send(f"Erreur lors de la récupération des informations pour le numéro: {phone_number}\nStatut de la réponse: {response.status_code}")
            return
        
        data = response.json()

        valid = "✅" if data.get('valid') else "❌"
        number = data.get('number', 'Inconnu')
        local_format = data.get('local_format', 'Inconnu')
        international_format = data.get('international_format', 'Inconnu')
        country_prefix = data.get('country_prefix', 'Inconnu')
        country_code = data.get('country_code', 'Inconnu')
        country_name = data.get('country_name', 'Inconnu')
        location = data.get('location', 'Inconnu')
        carrier = data.get('carrier', 'Inconnu')
        line_type = data.get('line_type', 'Inconnu')
        embed = discord.Embed(title=f"Informations pour le numéro: {phone_number}", color=discord.Color.green())
        embed.add_field(name="🔍 Valide", value=valid, inline=False)
        embed.add_field(name="📞 Numéro", value=number, inline=False)
        embed.add_field(name="🔢 Format local", value=local_format, inline=False)
        embed.add_field(name="🌐 Format international", value=international_format, inline=False)
        embed.add_field(name="➕ Préfixe pays", value=country_prefix, inline=False)
        embed.add_field(name="🇺🇸 Code pays", value=country_code, inline=False)
        embed.add_field(name="🌍 Nom du pays", value=country_name, inline=False)
        embed.add_field(name="📍 Localisation", value=location, inline=False)
        embed.add_field(name="📡 Opérateur", value=carrier, inline=False)
        embed.add_field(name="📱 Type de ligne", value=line_type, inline=False)
        embed.set_footer(text=f"👤 Sent by: {ctx.author.display_name}")

        await ctx.send(embed=embed)

    except requests.exceptions.RequestException as e:
        await ctx.send(f"Erreur lors de la récupération des informations pour le numéro: {phone_number}\nErreur: {e}")

@bot.command()
async def email(ctx, email_address: str):
    try:
        url = f'https://api.hunter.io/v2/email-verifier?email={email_address}&api_key={HUNTER_API_KEY}'
        response = requests.get(url)

        if response.status_code != 200:
            await ctx.send(f"Erreur lors de la récupération des informations pour l'e-mail: {email_address}\nStatut de la réponse: {response.status_code}")
            return
        
        data = response.json().get('data', {})

        result = data.get('result', 'Inconnu')
        score = data.get('score', 'Inconnu')
        email = data.get('email', 'Inconnu')
        domain = data.get('domain', 'Inconnu')
        disposable = data.get('disposable', 'Inconnu')
        webmail = data.get('webmail', 'Inconnu')
        mx_records = data.get('mx_records', 'Inconnu')
        smtp_server = data.get('smtp_server', 'Inconnu')
        smtp_check = data.get('smtp_check', 'Inconnu')
        accept_all = data.get('accept_all', 'Inconnu')
        block = data.get('block', 'Inconnu')
        gibberish = data.get('gibberish', 'Inconnu')
        pattern = data.get('pattern', 'Inconnu')

        embed = discord.Embed(title=f"Informations pour l'e-mail: {email_address}", color=discord.Color.blue())
        embed.add_field(name="📧 E-mail", value=email, inline=False)
        embed.add_field(name="📊 Score", value=score, inline=False)
        embed.add_field(name="🏢 Domaine", value=domain, inline=False)
        embed.add_field(name="♻️ Jetable", value=disposable, inline=False)
        embed.add_field(name="📬 Webmail", value=webmail, inline=False)
        embed.add_field(name="📦 MX Records", value=mx_records, inline=False)
        embed.add_field(name="📨 Serveur SMTP", value=smtp_server, inline=False)
        embed.add_field(name="✅ Vérification SMTP", value=smtp_check, inline=False)
        embed.add_field(name="📥 Accept All", value=accept_all, inline=False)
        embed.add_field(name="🚫 Bloqué", value=block, inline=False)
        embed.add_field(name="🗣️ Gibberish", value=gibberish, inline=False)
        embed.add_field(name="🔢 Pattern", value=pattern, inline=False)
        embed.set_footer(text=f"👤 Sent by: {ctx.author.display_name}")

        await ctx.send(embed=embed)

    except requests.exceptions.RequestException as e:
        await ctx.send(f"Erreur lors de la récupération des informations pour l'e-mail: {email_address}\nErreur: {e}")

@bot.command()
async def aboie(ctx, member: discord.Member):
    try:
        excluded_member_id = 1268299911347044426
        excluded_member_id = 1096860973811372062
        excluded_member_id = 498085260244811786
        if member.id == excluded_member_id:
            await ctx.send("Jsuis pas ta salope.")
            return
        webhook = await ctx.channel.create_webhook(name=member.display_name, avatar=await member.avatar.read())
        await webhook.send("Wouaf Wouaf")
        await webhook.delete()

    except discord.errors.Forbidden:
        await ctx.send("Je n'ai pas la permission de créer un webhook.")
    except discord.errors.HTTPException as e:
        await ctx.send(f"Erreur lors de la création ou de l'envoi du webhook: {e}")

@bot.command()
async def soumets(ctx, member: discord.Member):
    try:
        excluded_member_id = 1268299911347044426
        excluded_member_id = 1096860973811372062
        excluded_member_id = 498085260244811786
        if member.id == excluded_member_id:
            await ctx.send("Jsuis pas ta salope.")
            return
        webhook = await ctx.channel.create_webhook(name=member.display_name, avatar=await member.avatar.read())
        await webhook.send("Je me soumet à la NRevolution !")
        await webhook.delete()

    except discord.errors.Forbidden:
        await ctx.send("Je n'ai pas la permission de créer un webhook.")
    except discord.errors.HTTPException as e:
        await ctx.send(f"Erreur lors de la création ou de l'envoi du webhook: {e}")


@bot.command()
async def profil(ctx, member: discord.Member):
    if member is None:
        member = ctx.author
    try:
        user = await bot.fetch_user(member.id)
        banner_url = user.banner.url if user.banner else "Pas de bannière"
    except discord.HTTPException:
        banner_url = "Pas de bannière"

    pseudo_affichage = member.display_name
    vrai_pseudo = f"{member.name}#{member.discriminator}"
    date_creation = member.created_at.strftime("%d/%m/%Y")
    debut_token = base64.b64encode(str(member.id).encode()).decode()
    pfp_url = member.avatar.url if member.avatar else "Pas d'avatar"
    nitro = "Oui" if member.premium_since else "Non"
    roles = ', '.join([role.mention for role in member.roles if role.name != "@everyone"])
    embed = discord.Embed(title=f"Profil de {pseudo_affichage}", color=discord.Color.purple())
    embed.add_field(name="Pseudo", value=f"{pseudo_affichage}, {vrai_pseudo}", inline=False)
    embed.add_field(name="Bio", value="Non disponible", inline=False)
    embed.add_field(name="Date de création", value=date_creation, inline=False)
    embed.add_field(name="Début du Token", value=debut_token, inline=False)
    embed.add_field(name="PFP", value=f"[Cliquez ici pour voir l'avatar]({pfp_url})", inline=False)
    embed.add_field(name="Bannière", value=f"[Cliquez ici pour voir la bannière]({banner_url})", inline=False)
    embed.add_field(name="Nitro", value=nitro, inline=False)
    embed.add_field(name="Rôles", value=roles if roles else "Aucun rôle", inline=False)
    embed.set_footer(text=f"Bot Created by AKIRA, commande lancée par {ctx.author.display_name}")
    await ctx.send(embed=embed)

@bot.command()
async def server(ctx):
    guild = ctx.guild
    owner = guild.owner
    member_count = guild.member_count
    channel_count = len([channel for channel in guild.channels if isinstance(channel, discord.TextChannel) or isinstance(channel, discord.VoiceChannel)])
    category_count = len(guild.categories)
    role_count = len(guild.roles)
    embed = discord.Embed(title=f"Informations du serveur {guild.name}", color=discord.Color.blue())
    embed.add_field(name="Nom du serveur", value=guild.name, inline=False)
    embed.add_field(name="Propriétaire", value=owner.mention if owner else "Inconnu", inline=False)
    embed.add_field(name="Nombre de membres", value=member_count, inline=False)
    embed.add_field(name="Nombre de salons", value=channel_count, inline=False)
    embed.add_field(name="Nombre de catégories", value=category_count, inline=False)
    embed.add_field(name="Nombre de rôles", value=role_count, inline=False)
    embed.set_footer(text=f"Commande lancée par {ctx.author.display_name}")
    embed.set_footer(text=f"Bot Created by AKIRA, commande lancée par {ctx.author.display_name}")
    await ctx.send(embed=embed)


@bot.command()
async def maclookup(ctx, mac_address: str):
    try:
        url = f'https://api.wigle.net/api/v2/network/detail?mac={mac_address}'
        headers = {
            'Authorization': f'Basic {WIGGLE_API_TOKEN}'
        }
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            mac_data = response.json()
            if mac_data.get('success'):
                net_details = mac_data.get('results', [{}])[0]
                ssid = net_details.get('ssid', 'Inconnu')
                address = net_details.get('housenumber', 'Inconnu')
                city = net_details.get('city', 'Inconnu')
                region = net_details.get('region', 'Inconnu')
                country = net_details.get('country', 'Inconnu')
                frequency = net_details.get('frequency', 'Inconnu')
                first_seen = net_details.get('firsttime', 'Inconnu')
                last_seen = net_details.get('lasttime', 'Inconnu')
                embed = discord.Embed(title=f"Informations pour l'adresse MAC: {mac_address}", color=discord.Color.blue())
                embed.add_field(name="SSID", value=ssid, inline=False)
                embed.add_field(name="Adresse", value=address, inline=False)
                embed.add_field(name="Ville", value=city, inline=False)
                embed.add_field(name="Région", value=region, inline=False)
                embed.add_field(name="Pays", value=country, inline=False)
                embed.add_field(name="Fréquence", value=frequency, inline=False)
                embed.add_field(name="Première vue", value=first_seen, inline=False)
                embed.add_field(name="Dernière vue", value=last_seen, inline=False)
                embed.set_footer(text=f"👤 Sent by: {ctx.author.display_name}")

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"Aucune information trouvée pour l'adresse MAC: {mac_address}")
        else:
            await ctx.send(f"Erreur lors de la récupération des informations pour l'adresse MAC: {mac_address}\nStatut de la réponse: {response.status_code}")

    except requests.exceptions.RequestException as e:
        await ctx.send(f"Erreur lors de la récupération des informations pour l'adresse MAC: {mac_address}\nErreur: {e}")

@bot.command()
async def kiss(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Vous devez mentionner une personne !")
        return

    kiss_gifs = [
        "https://cdn.nekos.life/kiss/kiss_001.gif",
        "https://cdn.nekos.life/kiss/kiss_102.gif",
        "https://cdn.nekos.life/kiss/kiss_131.gif",
        "https://cdn.nekos.life/kiss/kiss_050.gif",
        "https://cdn.nekos.life/kiss/kiss_060.gif",
        "https://cdn.nekos.life/kiss/kiss_072.gif",
        "https://cdn.nekos.life/kiss/kiss_091.gif",
        "https://cdn.nekos.life/kiss/kiss_021.gif",
        "https://cdn.nekos.life/kiss/kiss_064.gif",
        "https://cdn.nekos.life/kiss/kiss_083.gif"
    ]

    embed = discord.Embed(
        description=f"**{ctx.author.name}** viens d'embrasser **{member.name}** :kiss:",
        color=discord.Color.dark_gray()
    )
    embed.set_image(url=random.choice(kiss_gifs))
    embed.set_footer(text="Bot Created by AKIRA")
    embed.timestamp = ctx.message.created_at

    await ctx.send(embed=embed)

# @bot.command()
# async def mcsuccess(ctx, *, text: str = None):
#     if text is None:
#         await ctx.send("Écrivez un texte pour la réalisation.")
#         return
    
#     if len(text) > 23:
#         await ctx.send("Le succès ne peut contenir que 23 caractères maximum.")
#         return
    
#     if len(text) < 2:
#         await ctx.send("Le succès doit contenir plus de 2 caractères.")
#         return

#     width, height = 480, 240
#     image = Image.new('RGB', (width, height), color = (255, 255, 255))
#     draw = ImageDraw.Draw(image)
#     font = ImageFont.load_default()

#     draw.text((10, 10), "Succès obtenu!", fill=(0, 0, 0), font=font)
#     draw.text((10, 50), text, fill=(0, 0, 0), font=font)

#     img_data = BytesIO()
#     image.save(img_data, format='PNG')
#     img_data.seek(0)
#     await ctx.send(file=discord.File(img_data, 'Achievement.png'))

# @bot.command()
# async def blague(ctx):
#     try:
#         url = 'https://blague.xyz/api/joke/random/'
        
#         headers = {
#             'Authorization': 'PHKgOQejoFh7ipfmOrzji9sRJkOEDd28M0IY6-klwjFojtkMFtfirTl.d4a3.Z--'
#         }

#         async with aiohttp.ClientSession() as session:
#             async with session.get(url, headers=headers) as response:
#                 if response.status == 200:
#                     json = await response.json()
#                     question = json['joke']['question']
#                     answer = json['joke']['answer']

#                     embed = discord.Embed(
#                         title=f"{ctx.author.name}, voici une blague pour vous.",
#                         color=discord.Color.dark_gray()
#                     )
#                     embed.add_field(name="Blague", value=question, inline=False)
#                     embed.add_field(name="Réponse", value=f"||{answer}||", inline=False)
#                     embed.set_footer(text="Blague fournie par blague.xyz")
#                     embed.timestamp = ctx.message.created_at

#                     await ctx.send(embed=embed)
#                 else:
#                     await ctx.send("Impossible de récupérer une blague pour le moment. Réessayez plus tard.")

#     except Exception as e:
#         await ctx.send(f"Une erreur s'est produite : {e}")

# @bot.command()
# async def cdox(ctx, *, pseudo: str):
#     try:
#         guild = ctx.guild
#         channel_name = pseudo.replace(" ", "-") 
#         new_channel = await guild.create_text_channel(channel_name)
        
#         embed = discord.Embed(title=f"{pseudo}", description=f"Channel pour {pseudo}", color=discord.Color.blue())
#         embed.set_footer(text=f"👤 Sent by: {ctx.author.display_name}")
        
#         await new_channel.send(embed=embed)
        
#         await ctx.send(f'Channel créé: {new_channel.mention}')

#     except discord.errors.Forbidden:
#         await ctx.send("Je n'ai pas la permission de créer un canal.")
#     except discord.errors.HTTPException as e:
#         await ctx.send(f"Erreur lors de la création du canal: {e}")

### ~8Ball~

answers = [
    'Il est certain.',
    'C\'est décidément ainsi.',
    'Sans aucun doute.',
    'Oui définitivement.',
    'Vous pouvez vous y fier.',
    'Comme je le vois oui.',
    'GalackQSM est le meilleur.',
    'Bonne perspective.',
    'Oui.',
    'Non.',
    'Les signes pointent vers Oui.',
    'Je sais pas.',
    'Répondre brumeux, réessayer.',
    'Demander à nouveau plus tard.',
    'Mieux vaut ne pas te dire maintenant.',
    'Impossible de prédire maintenant.',
    'Concentrez-vous et demandez à nouveau.',
    'Ne comptez pas dessus.',
    'Ma réponse est non.',
    'Mes sources disent non.',
    'Les perspectives ne sont pas si bonnes.',
    'Très douteux.'
]

@bot.command()
async def eightball(ctx, *, question: str = None):
    if not question:
        await ctx.send("Veuillez fournir une question à poser.")
        return

    answer = random.choice(answers)
    embed = discord.Embed(
        title='🎱 Je réponds à tes questions 🎱',
        color=discord.Color.blue()
    )
    embed.add_field(name='Question', value=question, inline=False)
    embed.add_field(name='Réponse', value=answer, inline=False)
    embed.set_footer(text=f"Commande lancée par {ctx.author.display_name}")
    
    await ctx.send(embed=embed)
    
#### ~Fun~

@bot.command()
async def chien(ctx):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://dog.ceo/api/breeds/image/random') as response:
                data = await response.json()
                img_url = data['message']
            
            embed = discord.Embed(
                title=f"{ctx.author.display_name} regarde un chien apparaître 🐶",
                color=discord.Color.blue()
            )
            embed.set_image(url=img_url)
            embed.set_footer(text=f"Commande lancée par {ctx.author.display_name} • {discord.utils.utcnow().strftime('%d/%m/%Y %H:%M:%S')}")
            
            await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"Un problème est survenu. Veuillez réessayer dans quelques secondes.\nErreur : {str(e)}")


### ~Osint~

@bot.command(name='dns')
async def dns_command(ctx, domain: str):
    try:
        results = shodan_api.search(f'hostname:{domain}')
        embed = discord.Embed(title=f"Résultats pour {domain}", color=discord.Color.blue())
        for result in results['matches']:
            embed.add_field(name=result.get('hostnames', 'N/A'), value=f"IP: {result['ip_str']}", inline=False)
        embed.set_footer(text="Données fournies par Shodan")
        await ctx.send(embed=embed)
    except shodan.APIError as e:
        await ctx.send(f"Erreur avec Shodan API: {e}")

### ~Ddos~

@bot.command(name='ddos')
async def ddos_command(ctx, host: str, time_in_seconds: int, method_name: str):
    if time_in_seconds > 200:
        await ctx.send("Le temps maximum est de 200 secondes.")
        return

    if time_in_seconds <= 0:
        await ctx.send("Le temps doit être supérieur à 0.")
        return

    payload = {
        'username': USERNAME,
        'key': KEY,
        'host': host,
        'port': 443,
        'time': time_in_seconds,
        'method': method_name
    }

    try:
        response = requests.get(API_URL, params=payload)
        if response.status_code == 200:
            await ctx.send("L'attaque a été envoyée avec succès.")
        else:
            await ctx.send(f"Erreur: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        await ctx.send(f"Erreur de connexion: {e}")
        


### ~Help~

@bot.command()
async def help(ctx):
    """Affiche la liste des commandes disponibles."""
    embed = discord.Embed(
        title="Liste des commandes",
        description="Voici les commandes disponibles pour ce bot.",
        color=discord.Color.blue()
    )
    
    embed.add_field(name=">mog <membre> <mode>", value="Moge un utilisateur en mode 'girl' ou 'haxor'.", inline=False)
    embed.add_field(name=">antiraid <on/off>", value="Active ou désactive l'anti-raid.", inline=False)
    embed.add_field(name=">demog <membre>", value="Démoge un utilisateur.", inline=False)
    embed.add_field(name=">searchmess <user_id>", value="Recherche les messages d'un utilisateur.", inline=False)
    embed.add_field(name=">ascii <texte>", value="Affiche un texte en ASCII art (max 20 caractères).", inline=False)
    embed.add_field(name=">wl <membre>", value="Ajoute un utilisateur à la liste des autorisés.", inline=False)
    embed.add_field(name=">unwl <membre>", value="Retire un utilisateur de la liste des autorisés.", inline=False)
    embed.add_field(name=">wllist", value="Affiche la liste des utilisateurs autorisés.", inline=False)
    embed.add_field(name=">search <query>", value="Recherche des informations via OSINT.", inline=False)
    embed.add_field(name=">iplookup <ip_address>", value="Recherche des informations pour une adresse IP.", inline=False)
    embed.add_field(name=">numinfo <phone_number>", value="Vérifie les informations d'un numéro de téléphone.", inline=False)
    embed.add_field(name=">email <email_address>", value="Vérifie les informations pour un e-mail.", inline=False)
    embed.add_field(name=">aboie <membre>", value="Envoie un message 'Wouaf Wouaf' via un webhook.", inline=False)
    embed.add_field(name=">soumets <membre>", value="Envoie un message 'Je me soumet à la NRevolution !' via un webhook.", inline=False)
    embed.add_field(name=">profil <membre>", value="Affiche le profil d'un utilisateur.", inline=False)
    embed.add_field(name=">server", value="Affiche les informations du serveur.", inline=False)
    embed.add_field(name=">maclookup <mac_address>", value="Recherche des informations pour une adresse MAC.", inline=False)
    embed.add_field(name=">kiss <membre>", value="Envoie un GIF de baiser à un utilisateur.", inline=False)
    embed.add_field(name=">eightball <question>", value="Répond à une question de manière aléatoire.", inline=False)
    
    embed.set_footer(text="Bot Created by AKIRA")
    await ctx.send(embed=embed)
    
async def start_bot(token):
    bot = commands.Bot(command_prefix='>', intents=intents, help_command=None)
    await bot.start(token)

for token in DISCORD_TOKENS:
    import asyncio
    asyncio.run(start_bot(token))

bot.run(TOKEN)
