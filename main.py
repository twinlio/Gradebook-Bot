import requests
from lxml import html
import hmac, hashlib, base64
from bs4 import BeautifulSoup
import discord
from discord.ext import commands
import os
from replit import db
import ast
from keep_alive import keep_alive

client = commands.Bot(command_prefix='!')

def text_num_split(item):
    for index, letter in enumerate(item, 0):
        if letter.isdigit():
            return [item[:index],item[index:]]


s=requests.Session()
def hash(password,contextdata):
    return hmac.new(contextdata.encode('ascii'), base64.b64encode(hashlib.md5(password.encode('ascii')).digest()).replace(b"=", b""), hashlib.md5).hexdigest()
def login(user,pw):
    global p
    url="https://powerschool.ash.nl/guardian/home.html"
    result = s.get(url)
    tree = html.fromstring(result.text)
    pstoken = list(set(tree.xpath("//*[@id=\"LoginForm\"]/input[1]/@value")))[0]
    contextdata = list(set(tree.xpath("//input[@id=\"contextData\"]/@value")))[0]
    new_pw=hash(pw,contextdata)
    payload={
    'pstoken':pstoken,
    'contextData':contextdata,
    'dbpw':new_pw,
    'ldappassword':pw,
    'account':user,
    'pw':pw
    }
    p = s.post(url, data=payload)

    soup = BeautifulSoup(p.text, 'lxml')

    valid_blocks = ('A(A)', 'B(A)', 'C(A)', 'D(A)', 'E(A)', 'F(A)', 'G(A)', 'H(A)')
    return_list = []
    for i in soup.find_all('tr', class_='center'): # Block
        for x in i.find_all('td', {'align': 'left'}): # CLass Name
            if i.td:
                if i.td.text in valid_blocks:
                    text = x.text
                    split_string = text.split("Email", 1)
                    block_fulltext = split_string[0]
                    for y in i.find_all('a', class_='bold'): # Grade
                        grade_list = text_num_split(y.text)
                        return_list.append([i.td.text.replace('(A)', ''), block_fulltext.rstrip(), grade_list[1], grade_list[0]])
    return return_list

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name='!help'))
    print(client.user)

@client.command()
async def setup(ctx, username=None, password=None):
    if ctx.channel.type is not discord.ChannelType.private:
        await ctx.send('You must be on a DM chat to exectue this command')
        return
    if username is None or password is None:
        await ctx.send('Invalid argumants. !setup <username> <password>')
        return
    # Section 1 - Set {Discord-UserID:[username,password]} varibale in db 
    dictionary = db["dict_userid:username-password"]
    dictionary = ast.literal_eval(dictionary)
    dictionary[f"{ctx.author.id}"] = [username, password]
    db["dict_userid:username-password"] = f"{dictionary}"
    await ctx.send('Your username and password has been saved.')


@client.command(aliases=['mg', 'mygrade'])
async def mygrades(ctx):
    if ctx.channel.type is not discord.ChannelType.private:
        await ctx.send('You must be on a DM chat to exectue this command')
        return
    dictionary = db["dict_userid:username-password"]
    dictionary = ast.literal_eval(dictionary)
    try:        
        information = dictionary[f'{ctx.author.id}']
        username = information[0]  
        password = information[1]      
    except KeyError:
        await ctx.send('You do not have a set username and password! Set one up by doing the command !setup <username> <password>')
        return
    list = login(username, password)
    embedVar = discord.Embed(title="Your Grades", description=" ", color=0x00ff00)
    for i in list:
        block = i[0]
        name = i[1]
        number_grade = i[2]
        letter_grade = i[3]
        formatted_class_name = f'{block} - {name}'
        formatted_grade = f'{number_grade}, {letter_grade}'
        embedVar.add_field(name=formatted_class_name, value=formatted_grade, inline=False)
    await ctx.send(embed=embedVar)


@client.command()
async def pledge(ctx):
    await ctx.send('"I pledge to not look at the database with the information of usernames and passwords or any sort of act that will leak any information such as username, password, grades, etc." - twinlio#3481')


@client.command(aliases=['feedback', 'bug'])
async def github(ctx):
    await ctx.send('For feedback, bug report, feature request, please visit: https://github.com/twinlio/Gradebook-Bot')


client.remove_command('help')
@client.command()
async def help(ctx):
    embedVar = discord.Embed(title="List of Commands", description=" ", color=0x00ff00)
    embedVar.add_field(name='!mygrades [mg]', value='Get the overall grade for all classes', inline=False)
    embedVar.add_field(name='!pledge', value="See the owner's pledge", inline=False)
    embedVar.add_field(name='!github', value="Get the link to the github", inline=False)
    await ctx.send(embed=embedVar)


@client.command()
async def membercount(ctx):
    num = 0
    if ctx.message.author.id == 299267793759764483:
        dicti = db["dict_userid:username-password"]
        dicti = ast.literal_eval(dicti)
        for i in dicti:
            num += 1
        await ctx.send(num)
    else:
        await ctx.send('You are not allowed to execute this command!')


keep_alive()
client.run(os.environ['BOTTOKEN'])
