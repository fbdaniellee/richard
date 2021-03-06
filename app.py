from distutils.command.config import config
from youtube_dl import cache
from telethon import TelegramClient, events, sync
import asyncio
import os
import zipfile
import re
import requests
from zipfile import ZipFile , ZipInfo 
import multiFile
import random
from bs4 import BeautifulSoup
import time
from pydownloader.downloader import Downloader
from datetime import datetime
import pytz
import infos
import Client
import traceback
from config import*
import S5Crypto
import mediafire

print(proxy)
if proxy == '':
	proxy_decrypt = ''
	pass
else:
	proxy_ = proxy.split('://')
	proxy_token = S5Crypto.decrypt(str(proxy_[1])).split(':')
	ip = proxy_token[0]
	port = proxy_token[1]
	proxy_decrypt = {'http':f'socks5://'+str(ip)+':'+str(port),'https':f'socks5://'+str(ip)+':'+str(port)}	
	print(proxy_decrypt)

IST=pytz.timezone('Cuba')

links =[]

Users_Data=[f'{USUARIO}',f'{USUARIO_ID}']

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

async def get_file_size(file):
    file_size = os.stat(file)
    return file_size.st_size

async def uploadFile(filename,currentBits,totalBits,speed,time,args):
	try:
	       bot = args[0]
	       uploadingInfo = infos.createUploading(filename,totalBits,currentBits,speed,time,originalfile)
	       await bot.edit(uploadingInfo)
	except Exception as ex:
	   print(str(ex))
	pass
	
async def upload_to_moodle(f,msg):
            #rand_user=Users_Data[random.randint(0,len(Users_Data)-1)]
            rand_user=Users_Data
            size = await get_file_size(f)
            try:
                moodle = Client.Client(rand_user[0],f'{PASSWORD}',proxy_decrypt)
                loged = moodle.login()
                if loged == True:
                    resp = moodle.upload_file(f,rand_user[1],progressfunc=uploadFile,args=(msg))
                    data=str(resp).replace('\\','')
                    await msg.edit(f'??? Subido ???\n\n????Archivo: {str(f)}\n????Tama??o Total: {str(sizeof_fmt(size))}\n\n????Usuario: <code>{USUARIO}</code> \n????Contrase??a: <code>{PASSWORD}</code>\n\n????Enlace:\n\n'+data, parse_mode="html") 
                    
                 
            except Exception as e:
                print(traceback.format_exc(),'Error en el upload')
                



async def process_file(file,bot,ev,msg):
    try:

        msgurls = ''
        maxsize = 1024 * 1024 * 1024 * 2
        file_size = await get_file_size(file)
        chunk_size = 1024 * 1024 * ZIP_MB
        #rand_user=Users_Data[random.randint(0,len(Users_Data)-1)]
        rand_user=Users_Data
        
        if file_size > chunk_size:
            await msg.edit(f'????Comprimiendo...\n\n????Archivo: {str(file)}\n\n????Tama??o Total: {str(sizeof_fmt(file_size))}\n\n????Partes: {len(multiFile.files)} - {str(sizeof_fmt(chunk_size))}')
            mult_file =  multiFile.MultiFile(file+'.7z',chunk_size)
            zip = ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
            zip.write(file)
            zip.close()
            mult_file.close()
            nuvContent = ''
            i = 0
            data=''
            for f in multiFile.files:
                await msg.edit(f'??????Subiendo...\n\n????Archivo: {str(f)}\n\n????Tama??o: {str(sizeof_fmt(file_size))}\n\n????Partes: {len(multiFile.files)}/{ZIP_MB} MB')
                moodle = Client.Client(rand_user[0], f'{PASSWORD}',proxy_decrypt)
                loged = moodle.login()
                if loged == True:
                    resp = moodle.upload_file(f,rand_user[1],proxy_decrypt)
                    data=data+'\n\n'+str(resp).replace('\\','')
                    
            await msg.edit(f'??? Subido ???\n\n????Archivo: {str(f)}\n????Tama??o: {str(sizeof_fmt(file_size))}\n\n????Usuario: <code>{USUARIO}</code>\n????Contrase??a: <code>{PASSWORD}</code>\n\n????Enlace:'+data, parse_mode="html")

        else:
            await upload_to_moodle(file,msg)
            os.unlink(file)

    except Exception as e:
            await msg.edit('(Error Subida) - ' + str(e))


async def processMy(ev,bot):
    try:
        text=ev.message.text
        message = await bot.send_message(ev.chat_id, '??????Procesando...')
        if ev.message.file:
            await message.edit('??????Descargando Archivo...')
            file_name = await bot.download_media(ev.message)
            await process_file(file_name,bot,ev,message)
    except Exception as e:
                        await bot.send_message(str(e))

def req_file_size(req):
    try:
        return int(req.headers['content-length'])
    except:
        return 0

def get_url_file_name(url,req):
    try:
        if "Content-Disposition" in req.headers.keys():
            return str(re.findall("filename=(.+)", req.headers["Content-Disposition"])[0])
        else:
            tokens = str(url).split('/');
            return tokens[len(tokens)-1]
    except:
           tokens = str(url).split('/');
           return tokens[len(tokens)-1]
    return ''

def save(filename,size):
    mult_file =  multiFile.MultiFile(filename+'.7z',size)
    zip = ZipFile(mult_file,  mode='w', compression=zipfile.ZIP_DEFLATED)
    zip.write(filename)
    zip.close()
    mult_file.close()

async def downloadFile(download,filename,currentBits,totalBits,speed,time,args):
	try:
		bot = args[0]
		msg = args[1]
		downloadingInfo = infos.createDownloading(filename,totalBits,currentBits,speed,time)
		await msg.edit(downloadingInfo)
	except Exception as ex:
	   print(str(ex))
	pass

async def ddl(msg,ev,bot,url):
	downloader = Downloader()
	file = await downloader.download_url(url,progressfunc=downloadFile,args=(bot,msg))
	if file:
	        await process_file(file,bot,ev,msg)
         
async def lista(ev,bot,msg):
    global links
    for message in links:
        try:
            multiFile.clear()
            text = message.message.text
            if message.message.file:
                msg = await bot.send_message(ev.chat_id,"??????Descargando..."+text)
                file_name = await bot.download_media(message.message)
                await process_file(file_name,bot,ev,msg)      
        except Exception as e:
            await bot.send_message(ev.chat_id,e)
    links=[]                 

    
bot = TelegramClient( 
    'bot', api_id=API_ID, api_hash=API_HASH).start(bot_token =BOT_TOKEN ) 
 
action = 0
actual_file = ''

@bot.on(events.NewMessage()) 
async def process(ev: events.NewMessage.Event):
    global links
    text = ev.message.text
    file = ev.message.file
    url = ev.message.text
    multiFile.clear()
    user_id = ev.message.peer_id.user_id
    if user_id in OWNER:
        if '#watch' in text:
            await bot.send_message(ev.chat_id,'????Esperando...')

        elif 'mediafire' in url:
            await bot.send_message(ev.chat_id,'Procesando enlace de MEDIAFIRE...')
            url = mediafire.get('url')
            directurl = mediafire.get('mediafireurl')

        elif 'https' in text or 'http' in text:
            msg= await bot.send_message(ev.chat_id,'Procesando Enlace...')
            await ddl(msg,bot,ev,url=text) 

        elif file:
            await bot.send_message(ev.chat_id,'Archivo Encontrado... /up')
            links.append(ev)   

        elif ev.message.file:
            links.append(ev)    
            #await processMy(ev,bot)
        elif '#clear' in text:
            links=[]
        
@bot.on(events.NewMessage(pattern='/info'))
async def info(ev: events.NewMessage.Event):
    print('info...')
    user_id = ev.message.peer_id.user_id
    if user_id in OWNER:

        await bot.send_message(ev.chat_id,f'???Informaci??n???\n\n????Moodle: {MOODLE_URL}\n????Usuario: <code>{USUARIO}</code>\n????Contrase??a: <code>{PASSWORD}</code>\n????Tama??o de zip: {ZIP_MB}',parse_mode='HTML') 
    else:
        await bot.send_message(ev.chat_id,'??????Acceso Denegado??????')   

@bot.on(events.NewMessage(pattern='/start'))
async def process(ev: events.NewMessage.Event):
    print('start...')
    user_id = ev.message.peer_id.user_id
    if user_id in OWNER:
        Hora=str(datetime.now(IST).time()).split(".")
        Hora.pop(-1)
        h="".join(map(str, Hora))
        
        
        await bot.send_message(ev.chat_id,f'??? Se inicio correctamente el Bot ???\n\n???Usa /help para aprender sobre mis funciones.')
    else:
        await bot.send_message(ev.chat_id,'??????Acceso Denegado??????') 

@bot.on(events.NewMessage(pattern='/pro'))
async def process(ev: events.NewMessage.Event):  
    user_id = ev.message.peer_id.user_id
    if user_id in OWNER:
        await bot.send_message(ev.chat_id, f'????Procesos:\n\n{len(links)}\n\n/up\n/clear')  
    else: 
        await bot.send_message(ev.chat_id,'??????Acceso Denegado??????')
         
@bot.on(events.NewMessage(pattern='/add_proxy'))
async def process(ev: events.NewMessage.Event):
	proxy_new = ev.message.text.split(' ')[1]
	if proxy!='':
		proxy = proxy_new
	else:
		proxy = ''
	await bot.send_message(ev.chat.id,'Proxy quitado!')
	print(proxy)

@bot.on(events.NewMessage(pattern='/clear'))
async def process(ev: events.NewMessage.Event):  
    user_id = ev.message.peer_id.user_id
    if user_id in OWNER:
        await bot.send_message(ev.chat_id, f'???? {len(links)} Procesos Limpiados ????\n/pro')
        links.clear()
    else:
        await bot.send_message(ev.chat_id,'??????Acceso Denegado??????')
    


@bot.on(events.NewMessage(pattern='/up'))
async def process(ev: events.NewMessage.Event):
    print('Up...') 
    user_id = ev.message.peer_id.user_id
    if user_id in OWNER:
        msg = await bot.send_message(ev.chat_id,'????Analizando...')
        await lista(ev,bot,msg)
    else:
        await bot.send_message(ev.chat_id,'??????Acceso Denegado??????')



print('App Run...')
bot.loop.run_forever()


