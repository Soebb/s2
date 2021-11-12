from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os
import shutil
from pymkv import MKVFile
import time
import math
from pyromod import listen
import re
import asyncio
import youtube_dl
import pysubs2
from moviepy.editor import *

if "BOT_TOKEN" in os.environ:
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    API_ID = os.environ.get("API_ID")
    API_HASH = os.environ.get("API_HASH")
else:
    BOT_TOKEN = " "
    API_ID = " "
    API_HASH = " "


YTDL_REGEX = (r"^((?:https?:)?\/\/)"
              r"?((?:www|m)\.)"
              r"?((?:youtube\.com|youtu\.be|xvideos\.com|pornhub\.com"
              r"|xhamster\.com|xnxx\.com))"
              r"(\/)([-a-zA-Z0-9()@:%_\+.~#?&//=]*)([\w\-]+)(\S+)?$")

progress_pattern = re.compile(
    r'(frame|fps|size|time|bitrate|speed)\s*\=\s*(\S+)'
)

def parse_progress(line):
    items = {
        key: value for key, value in progress_pattern.findall(line)
    }
    if not items:
        return None
    return items

async def readlines(stream):
    pattern = re.compile(br'[\r\n]+')

    data = bytearray()
    while not stream.at_eof():
        lines = pattern.split(data)
        data[:] = lines.pop(-1)

        for line in lines:
            yield line

        data.extend(await stream.read(1024))

async def read_stderr(start, msg, process):
    async for line in readlines(process.stderr):
            line = line.decode('utf-8')
            progress = parse_progress(line)
            if progress:
                #Progress bar logic
                now = time.time()
                diff = start-now
                text = 'PROGRESS\n'
                text += 'Size : {}\n'.format(progress['size'])
                text += 'Time : {}\n'.format(progress['time'])
                text += 'Speed : {}\n'.format(progress['speed'])

                if round(diff % 5)==0:
                    try:
                        await msg.edit( text )
                    except:
                        pass

async def progress_bar(current, total, text, message, start):

    now = time.time()
    diff = now-start
    if round(diff % 10) == 0 or current == total:
        percentage = current*100/total
        speed = current/diff
        elapsed_time = round(diff)*1000
        eta = round((total-current)/speed)*1000
        ett = eta + elapsed_time

        elapsed_time = TimeFormatter(elapsed_time)
        ett = TimeFormatter(ett)

        progress = "[{0}{1}] \n\n🔹Progress: {2}%\n".format(
            ''.join(["◼️" for i in range(math.floor(percentage / 5))]),
            ''.join(["◻️" for i in range(20 - math.floor(percentage / 5))]),
            round(percentage, 2))

        tmp = progress + "{0} of {1}\n\n️🔹Speed: {2}/s\n\n🔹ETA: {3}\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            # elapsed_time if elapsed_time != '' else "0 s",
            ett if ett != '' else "0 s"
        )

        try :
            await message.edit(
                text = '{}.\n{}'.format(text, tmp)
            )
        except:
            pass

def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]


Bot = Client(
    "Bot",
    bot_token = BOT_TOKEN,
    api_id = API_ID,
    api_hash = API_HASH
)


START_TXT = """
Hi {}, I'm Forward Tag Remover bot.\n\nForward me some messages, i will remove forward tag from them.\nAlso can do it in channels.
"""

START_BTN = InlineKeyboardMarkup(
        [[
        InlineKeyboardButton('Source Code', url='https://github.com/samadii/ChannelForwardTagRemover'),
        ]]
    )


@Bot.on_message(filters.command(["start"]))
async def start(bot, update):
    text = START_TXT.format(update.from_user.mention)
    reply_markup = START_BTN
    await update.reply_text(
        text=text,
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )

sub = None
vid = False
Url = None
"""
@Bot.on_message(filters.private & filters.video)
async def vide(client, message):
    global vid
    global sub
    if vid != None:
        return
    chat_id = message.from_user.id
    start_time = time.time()
    downloading = await client.send_message(chat_id, 'Downloading your File!')
    video = await client.download_media(
        message = message,
        file_name = "temp/vid1.mkv",
        progress = progress_bar,
        progress_args = (
            'Initializing',
            downloading,
            start_time
            )
        )

    if video is None:
        return client.edit_message_text(
            text = 'Downloading Failed!',
            chat_id = chat_id,
            message_id = downloading.message_id
        )
    cut = await bot.ask(message.chat.id,'زمان آغار و پایان برش؟', filters=filters.text)
    os.system(f"ffmpeg -ss {cut.text.split()[0]} -i temp/vid1.mkv -ss 00:01:00 -t {cut.text.split()[1]} -c copy temp/vid2.mkv")
    merge = await bot.ask(message.chat.id,'ویدیویی که میخوای ادغام شه؟بفرس', filters=filters.video)
    await client.download_media(message=message, file_name="temp/vid3.mkv")
    subprocess.call(
        ['ffmpeg', '-f', 'concat', '-i', 'temp/inputs.txt', '-c', 'copy', 'temp/out.mkv']
    )
    if (sub == None) or (vid == None):
        return
    text = 'Your File is Being Hard Subbed. This might take a long time!'
    sent_msg = await client.send_message(chat_id, text)

    command = [
            'ffmpeg','-hide_banner',
            '-i','temp/out.mkv',
            '-vf',"subtitles=temp/sub.ass"+":fontsdir=temp:force_style='Fontname=B Titr,Fontsize=28,PrimaryColour=&H0000FFFF,Shadow=0'", #,SecondaryColour=&H0300FFFF'", #,OutlineColour=&H00000000,BackColour=&H02000000,ScaleX=100,ScaleY=100,BorderStyle=1,Outline=1,Alignment=2,MarginL=10,MarginR=10,MarginV=10,Encoding=1'",
            '-c:v','h264',
            '-map','0:v:0',
            '-map','0:a:0?',
            #'-crf','18',
            '-preset','faster',
            '-y','temp/final.mkv'
            ]
    process = await asyncio.create_subprocess_exec(
            *command,
            # stdout must a pipe to be accessible as process.stdout
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            )
    await asyncio.wait([
            read_stderr(start,msg, process),
            process.wait(),
        ])
    if process.returncode == 0:
        await message.reply('Muxing  Completed Successfully!')
    else:
        return await message.reply('An Error occured while Muxing!')
    text = 'Your File is Being Hard Subbed. This might take a long time!'
    sent_msg = await client.send_message(chat_id, text)
    start_time = time.time()
    try:
        await client.send_video(chat_id, progress = progress_bar, progress_args = ('Uploading your File!',sent_msg,start_time), video = 'temp/final.mkv', height = 720, width = 1280, file_name = re.sub(r'\S*0p\S*|\S*0P\S*', '720P', sub+'.mkv').replace('.ass', '').replace('.srt', '') if sub.__contains__('0p') or sub.__contains__('0P') else sub.replace('.ass', '').replace('.srt', '')+"720P.mkv")
        text = 'File Successfully Uploaded!\nTotal Time taken : {} seconds'.format(round(time.time()-start_time))
        await sent_msg.edit(text)
    except Exception as e:
        print(e)
        await client.send_message(chat_id, 'An error occured while uploading the file!\nCheck logs for details of the error!')
    sent_msg = await client.send_message(chat_id, text)
    start_time = time.time()
    try:
        await client.send_video(chat_id, progress = progress_bar, progress_args = ('Uploading your File!',sent_msg,start_time), video = 'temp/final.mkv', height = 300, width = 536, file_name = re.sub(r'\S*0p\S*|\S*0P\S*', '240P', sub+'.mkv').replace('.ass', '').replace('.srt', '') if sub.__contains__('0p') or sub.__contains__('0P') else sub.replace('.ass', '').replace('.srt', '')+"240P.mkv")
        
        text = 'File Successfully Uploaded!\nTotal Time taken : {} seconds'.format(round(time.time()-start_time))
        await sent_msg.edit(text)
    except Exception as e:
        print(e)
        await client.send_message(chat_id, 'An error occured while uploading the file!\nCheck logs for details of the error!')
    sent_msg = await client.send_message(chat_id, text)
    start_time = time.time()
    try:
        await client.send_video(chat_id, progress = progress_bar, progress_args = ('Uploading your File!',sent_msg,start_time), video = 'temp/final.mkv', height = 480, width = 856, file_name = re.sub(r'\S*0p\S*|\S*0P\S*', '480P', sub+'.mkv').replace('.ass', '').replace('.srt', '') if sub.__contains__('0p') or sub.__contains__('0P') else sub.replace('.ass', '').replace('.srt', '')+"480P.mkv")
        
        text = 'File Successfully Uploaded!\nTotal Time taken : {} seconds'.format(round(time.time()-start_time))
        await sent_msg.edit(text)
    except Exception as e:
        print(e)
        await client.send_message(chat_id, 'An error occured while uploading the file!\nCheck logs for details of the error!')
    sent_msg = await client.send_message(chat_id, text)
    start_time = time.time()
    try:
        await client.send_video(chat_id, progress = progress_bar, progress_args = ('Uploading your File!',sent_msg,start_time), video = 'temp/final.mkv', height = 1080, width = 1920, file_name = re.sub(r'\S*0p\S*|\S*0P\S*', '1080P', sub+'.mkv').replace('.ass', '').replace('.srt', '') if sub.__contains__('0p') or sub.__contains__('0P') else sub.replace('.ass', '').replace('.srt', '')+"1080P.mkv")
        text = 'File Successfully Uploaded!\nTotal Time taken : {} seconds'.format(round(time.time()-start_time))
        await sent_msg.edit(text)
    except Exception as e:
        print(e)
        await client.send_message(chat_id, 'An error occured while uploading the file!\nCheck logs for details of the error!')

    sub = None
    vid = None
"""
@Bot.on_message(filters.private & filters.document)
async def subts(client, message):
    global sub
    global vid
    #global Url
    #if sub != None:
    #return
    if vid != False:
        os.remove("temp/sub.ass")
        vid = False
    ext = message.document.file_name.split('.').pop()
    if not ext in ['ass','srt']:
        return await message.reply("document just should be .ass or .srt!")
    ext = message.document.file_name.rsplit(".", 1)[1]
    chat_id = message.from_user.id
    start_time = time.time()
    downloading = await client.send_message(chat_id, 'Downloading your File!')
    Sub = await client.download_media(
        message = message,
        file_name = "temp/sub1."+ext,
        progress = progress_bar,
        progress_args = (
            'Initializing',
            downloading,
            start_time
            )
        )

    if Sub is None:
        return client.edit_message_text(
            text = 'Downloading Failed!',
            chat_id = chat_id,
            message_id = downloading.message_id
        )
    os.system(f"ffmpeg -i temp/sub1.{ext} temp/subt.ass")
    subs = pysubs2.load("temp/subt.ass", encoding="utf-8")
    for line in subs:
        if (not line.text.__contains__("color")) and (not line.text.__contains__("macvin")):
            line.text = line.text + "\\N{\\b1\\c&H0080ff&}t.me/dlmacvin_new{\\c}{\\b0}"
        
        if "color" in line.text:
            line.text = line.text.split('color')[0] + "{\\b1\\c&H0080ff&}t.me/dlmacvin_new{\\c}{\\b0}"
    subs.save("temp/sub.ass")
    try:
        os.remove("temp/subt.ass")
    except:
        pass
    
    await client.edit_message_text(
        text = "لینک یوتیوب ویدیو؟بفرس",
        chat_id = chat_id,
        message_id = downloading.message_id
    )
    sub = message.document.file_name
    """
    if vid != None and sub != None:
        text = 'Your File is Being Hard Subbed. This might take a long time!'
        sent_msg = await client.send_message(chat_id, text)
        start_time = time.time()
        try:
            await client.send_video(chat_id, progress = progress_bar, progress_args = ('Uploading your File!',sent_msg,start_time), video = 'temp/final.mkv', height = 720, width = 1280, file_name = re.sub(r'\S*0p\S*|\S*0P\S*', '720P', sub+'.mkv').replace('.ass', '').replace('.srt', '') if sub.__contains__('0p') or sub.__contains__('0P') else sub.replace('.ass', '').replace('.srt', '')+"720P.mkv")
            text = 'File Successfully Uploaded!\nTotal Time taken : {} seconds'.format(round(time.time()-start_time))
            await sent_msg.edit(text)
        except Exception as e:
            print(e)
            await client.send_message(chat_id, 'An error occured while uploading the file!\nCheck logs for details of the error!')
        sent_msg = await client.send_message(chat_id, text)
        start_time = time.time()
        try:
            await client.send_video(chat_id, progress = progress_bar, progress_args = ('Uploading your File!',sent_msg,start_time), video = 'temp/final.mkv', height = 300, width = 536, file_name = re.sub(r'\S*0p\S*|\S*0P\S*', '240P', sub+'.mkv').replace('.ass', '').replace('.srt', '') if sub.__contains__('0p') or sub.__contains__('0P') else sub.replace('.ass', '').replace('.srt', '')+"240P.mkv")
            text = 'File Successfully Uploaded!\nTotal Time taken : {} seconds'.format(round(time.time()-start_time))
            await sent_msg.edit(text)
        except Exception as e:
            print(e)
            await client.send_message(chat_id, 'An error occured while uploading the file!\nCheck logs for details of the error!')
        sent_msg = await client.send_message(chat_id, text)
        start_time = time.time()
        try:
            await client.send_video(chat_id, progress = progress_bar, progress_args = ('Uploading your File!',sent_msg,start_time), video = 'temp/final.mkv', height = 480, width = 856, file_name = re.sub(r'\S*0p\S*|\S*0P\S*', '480P', sub+'.mkv').replace('.ass', '').replace('.srt', '') if sub.__contains__('0p') or sub.__contains__('0P') else sub.replace('.ass', '').replace('.srt', '')+"480P.mkv")

            text = 'File Successfully Uploaded!\nTotal Time taken : {} seconds'.format(round(time.time()-start_time))
            await sent_msg.edit(text)
        except Exception as e:
            print(e)
            await client.send_message(chat_id, 'An error occured while uploading the file!\nCheck logs for details of the error!')
        sent_msg = await client.send_message(chat_id, text)
        start_time = time.time()
        try:
            await client.send_video(chat_id, progress = progress_bar, progress_args = ('Uploading your File!',sent_msg,start_time), video = 'temp/final.mkv', height = 1080, width = 1920, file_name = re.sub(r'\S*0p\S*|\S*0P\S*', '1080P', sub+'.mkv').replace('.ass', '').replace('.srt', '') if sub.__contains__('0p') or sub.__contains__('0P') else sub.replace('.ass', '').replace('.srt', '')+"1080P.mkv")
            text = 'File Successfully Uploaded!\nTotal Time taken : {} seconds'.format(round(time.time()-start_time))
            await sent_msg.edit(text)
        except Exception as e:
            print(e)
            await client.send_message(chat_id, 'An error occured while uploading the file!\nCheck logs for details of the error!')
        sub = None
        vid = None
    """


@Bot.on_message(filters.private & filters.regex(YTDL_REGEX))
async def urlss(client, message):
    global sub
    global vid
    vids = ''
    #global Url
    #if Url != None:
    #return
    
    try:
        os.remove("temp/vid720.mp4")
    except:
        pass
    try:
        os.remove("temp/vid1080.mp4")
    except:
        pass
    try:
        os.remove("temp/vid240.mp4")
    except:
        pass
    try:
        os.remove("temp/vid480.mp4")
    except:
        pass
    chat_id = message.from_user.id
    
    Url = message.text
    cut = await client.ask(message.chat.id,'زمان آغار و پایان برش؟', filters=filters.text)
    preview_video = await client.ask(message.chat.id,'ویدیویی که میخوای ادغام شه؟بفرس', filters=filters.video)
    mess = await message.reply("cutting and merging...")
    await client.download_media(message=preview_video.video, file_name="temp/vid720.mp4")
    preview_video = await client.ask(message.chat.id,'ویدیویی که میخوای ادغام شه؟بفرس', filters=filters.video)
    mess = await message.reply("cutting and merging...")
    await client.download_media(message=preview_video.video, file_name="temp/vid2.mp4")

    opts1080 = {
        'format': 'best[height<=1080]',
        'geo_bypass':True,
        'nocheckcertificate':True,
        'videoformat':'mp4',
        'outtmpl': 'temp/vid1.mp4'
    }
    opts720 = {
        'format': 'best[height<=720]',
        'geo_bypass':True,
        'nocheckcertificate':True,
        'videoformat':'mp4',
        'outtmpl': 'temp/vid1.mp4'
    }
    opts480 = {
        'format': 'best[height<=480]',
        'geo_bypass':True,
        'nocheckcertificate':True,
        'videoformat':'mp4',
        'outtmpl': 'temp/vid1.mp4'
    }
    opts240 = {
        'format': 'best[height<=240]',
        'geo_bypass':True,
        'nocheckcertificate':True,
        'videoformat':'mp4',
        'outtmpl': 'temp/vid1.mp4'
    }
    trim_command = [
        "ffmpeg",
        "-i",
        "temp/vid1.mp4",
        "-ss",
        cut.text.split()[0],
        "-to",
        cut.text.split()[1],
        "-c",
        "copy",
        "-copyts",
        "temp/vid720.mp4"
    ]

    merge_command = [
        "ffmpeg",
        "-f",
        "concat",
        "-i",
        "temp/inputs.txt",
        "-c",
        "copy",
        "-y",
        "temp/out.mp4"
    ]
    name1080 = re.sub(r'\S*0p\S*|\S*0P\S*', '1080P', sub+'.mkv').replace('.ass', '').replace('.srt', '') if sub.__contains__('0p') or sub.__contains__('0P') else sub.replace('.ass', '').replace('.srt', '')+" 1080P.mkv"
    name240 = re.sub(r'\S*0p\S*|\S*0P\S*', '240P', sub+'.mkv').replace('.ass', '').replace('.srt', '') if sub.__contains__('0p') or sub.__contains__('0P') else sub.replace('.ass', '').replace('.srt', '')+" 240P.mkv"
    name720 = re.sub(r'\S*0p\S*|\S*0P\S*', '720P', sub+'.mkv').replace('.ass', '').replace('.srt', '') if sub.__contains__('0p') or sub.__contains__('0P') else sub.replace('.ass', '').replace('.srt', '')+" 720P.mkv"
    name480 = re.sub(r'\S*0p\S*|\S*0P\S*', '480P', sub+'.mkv').replace('.ass', '').replace('.srt', '') if sub.__contains__('0p') or sub.__contains__('0P') else sub.replace('.ass', '').replace('.srt', '')+" 480P.mkv"

    try:
        #os.system("mp4box -add temp/vid3.mp4 -cat temp/vid2.mp4 temp/out.mp4")
        
        process = await asyncio.create_subprocess_exec(
            *merge_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        #mkv1 = MKVFile('temp/vid3.mkv')
        #mkv2 = MKVFile('temp/vid2.mkv')
        #mkv1.add_file(mkv2)
        #mkv1.mux('temp/out.mkv')

        text = 'Your File is Being Hard Subbed. This might take a long time!'
        sent_msg = await client.send_message(chat_id, text)
        await mess.delete()
        os.system('''ffmpeg -hide_banner -i temp/out.mp4 -vf "subtitles=temp/sub.ass:fontsdir=temp/font:force_style='Fontname=B Titr,Fontsize=28,PrimaryColour=&H0000FFFF,Shadow=0'" -c:v h264 -map 0:v:0 -map 0:a:0? -preset faster -y temp/final.mp4''')
        os.system("ffmpeg -i temp/final.mp4 -y temp/final.mkv")
        await client.send_video(chat_id, video = 'temp/final.mkv', height = 720, width = 1280, file_name = name720, caption = name720)
        await sent_msg.delete()
    except Exception as e:
        print(e)
        await client.send_message(chat_id, 'An error occured!\nCheck logs for details of the error!')
        pass
    return
    try:
        os.remove("temp/inputs.txt")
    except:
        pass
    try:
        os.remove("temp/vid1.mp4")
    except:
        pass
    try:
        shutil.copyfile("temp/final.mkv", "files/"+name720)
    except Exception as e:
        print(e)
        pass
    trim_command = [
        "ffmpeg",
        "-i",
        "temp/vid1.mp4",
        "-ss",
        cut.text.split()[0],
        "-to",
        cut.text.split()[1],
        "-c",
        "copy",
        "-copyts",
        "temp/vid1080.mp4"
    ]
    try:
        with youtube_dl.YoutubeDL(opts1080) as ytdl:
            ytdl.extract_info(Url, download=True)
        process = await asyncio.create_subprocess_exec(
            *trim_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        #clip1 = VideoFileClip("temp/vid3.mp4")
        #clip2 = VideoFileClip("temp/vid2.mp4")
        #Merge = concatenate_videoclips([clip1, clip2])
        #Merge.write_videofile("temp/out.mp4")
        f = open("temp/inputs.txt", "w", encoding="utf-8")
        f.write(f"file '{vids.splitlines()[0]}'" + "\n" + "file 'temp/vid1080.mp4'")

        process = await asyncio.create_subprocess_exec(
            *merge_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        #mkv1 = MKVFile('temp/vid3.mkv')
        #mkv2 = MKVFile('temp/vid2.mkv')
        #mkv1.add_file(mkv2)
        #mkv1.mux('temp/out.mkv')
        text = 'Your File is Being Hard Subbed. This might take a long time!'
        sent_msg = await client.send_message(chat_id, text)
        await mess.delete()
        os.system('''ffmpeg -hide_banner -i temp/out.mp4 -vf "subtitles=temp/sub.ass:fontsdir=temp/font:force_style='Fontname=B Titr,Fontsize=28,PrimaryColour=&H0000FFFF,Shadow=0'" -c:v h264 -map 0:v:0 -map 0:a:0? -preset faster -y temp/final.mp4''')
        os.system("ffmpeg -i temp/final.mp4 -y temp/final.mkv")
        await client.send_video(chat_id, video = 'temp/final.mkv', height = 1080, width = 1920, file_name = name1080, caption = name1080)
        await sent_msg.delete()
    except Exception as e:
        print(e)
        await client.send_message(chat_id, 'An error occured!\nCheck logs for details of the error!')
        pass
    try:
        os.remove("temp/vid1.mp4")
    except:
        pass
    try:
        shutil.copyfile("temp/final.mkv", "files/"+name1080)
    except Exception as e:
        print(e)
        pass
    try:
        os.remove("temp/inputs.txt")
    except:
        pass
    trim_command = [
        "ffmpeg",
        "-i",
        "temp/vid1.mp4",
        "-ss",
        cut.text.split()[0],
        "-to",
        cut.text.split()[1],
        "-c",
        "copy",
        "-copyts",
        "temp/vid240.mp4"
    ]
    try:
        with youtube_dl.YoutubeDL(opts240) as ytdl:
            ytdl.extract_info(Url, download=True)
        process = await asyncio.create_subprocess_exec(
            *trim_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        #clip1 = VideoFileClip("temp/vid3.mp4")
        #clip2 = VideoFileClip("temp/vid2.mp4")
        #Merge = concatenate_videoclips([clip1, clip2])
        #Merge.write_videofile("temp/out.mp4")
        f = open("temp/inputs.txt", "w", encoding="utf-8")
        f.write(f"file '{vids.splitlines()[0]}'" + "\n" + "file 'temp/vid240.mp4'")
        process = await asyncio.create_subprocess_exec(
            *merge_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        #mkv1 = MKVFile('temp/vid3.mkv')
        #mkv2 = MKVFile('temp/vid2.mkv')
        #mkv1.add_file(mkv2)
        #mkv1.mux('temp/out.mkv')
        text = 'Your File is Being Hard Subbed. This might take a long time!'
        sent_msg = await client.send_message(chat_id, text)
        await mess.delete()
        os.system('''ffmpeg -hide_banner -i temp/out.mp4 -vf "subtitles=temp/sub.ass:fontsdir=temp/font:force_style='Fontname=B Titr,Fontsize=28,PrimaryColour=&H0000FFFF,Shadow=0'" -c:v h264 -map 0:v:0 -map 0:a:0? -preset faster -y temp/final.mp4''')
        os.system("ffmpeg -i temp/final.mp4 -y temp/final.mkv")
        await client.send_video(chat_id, video = 'temp/final.mkv', height = 300, width = 536, file_name = name240, caption = name240)
        await sent_msg.delete()
    except Exception as e:
        print(e)
        await client.send_message(chat_id, 'An error occured!\nCheck logs for details of the error!')
        pass
    try:
        os.remove("temp/vid1.mp4")
    except:
        pass
    try:
        shutil.copyfile("temp/final.mkv", "files/"+name240)
    except Exception as e:
        print(e)
        pass
    try:
        os.remove("temp/inputs.txt")
    except:
        pass
    trim_command = [
        "ffmpeg",
        "-i",
        "temp/vid1.mp4",
        "-ss",
        cut.text.split()[0],
        "-to",
        cut.text.split()[1],
        "-c",
        "copy",
        "-copyts",
        "temp/vid480.mp4"
    ]
    try:
        with youtube_dl.YoutubeDL(opts480) as ytdl:
            ytdl.extract_info(Url, download=True)
        process = await asyncio.create_subprocess_exec(
            *trim_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        #clip1 = VideoFileClip("temp/vid3.mp4")
        #clip2 = VideoFileClip("temp/vid2.mp4")
        #Merge = concatenate_videoclips([clip1, clip2])
        #Merge.write_videofile("temp/out.mp4")
        f = open("temp/inputs.txt", "w", encoding="utf-8")
        f.write(f"file '{vids.splitlines()[0]}'" + "\n" + "file 'temp/vid480.mp4'")
        process = await asyncio.create_subprocess_exec(
            *merge_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        #mkv1 = MKVFile('temp/vid3.mkv')
        #mkv2 = MKVFile('temp/vid2.mkv')
        #mkv1.add_file(mkv2)
        #mkv1.mux('temp/out.mkv')
        text = 'Your File is Being Hard Subbed. This might take a long time!'
        sent_msg = await client.send_message(chat_id, text)
        await mess.delete()
        os.system('''ffmpeg -hide_banner -i temp/out.mp4 -vf "subtitles=temp/sub.ass:fontsdir=temp/font:force_style='Fontname=B Titr,Fontsize=28,PrimaryColour=&H0000FFFF,Shadow=0'" -c:v h264 -map 0:v:0 -map 0:a:0? -preset faster -y temp/final.mp4''')
        os.system("ffmpeg -i temp/final.mp4 -y temp/final.mkv")
        await client.send_video(chat_id, video = 'temp/final.mkv', height = 480, width = 856, file_name = name480, caption = name480)
        await sent_msg.delete()
    except Exception as e:
        print(e)
        await client.send_message(chat_id, 'An error occured!\nCheck logs for details of the error!')
        pass
    try:
        os.remove("temp/vid1.mp4")
    except:
        pass
    try:
        shutil.copyfile("temp/final.mkv", "files/"+name480)
    except Exception as e:
        print(e)
        pass
    try:
        os.remove("temp/inputs.txt")
    except:
        pass
    
    try:
        for i in range(80):
            shutil.copy2('files/'+name480, f'files/{i}{name480}')
    except Exception as e:
        print(e)
        pass





    vid = True
    # Marhale Do
    
    if len(vids.splitlines()) == 1:
        return
    try:
        
        #os.system("mp4box -add temp/vid3.mp4 -cat temp/vid2.mp4 temp/out.mp4")
        
        #clip1 = VideoFileClip(f"vids.splitlines()[0]")
        #clip2 = VideoFileClip("temp/vid2.mp4")
        #Merge = concatenate_videoclips([clip1, clip2])
        #Merge.write_videofile("temp/out.mp4")
        f = open("temp/inputs.txt", "w", encoding="utf-8")
        f.write(f"file '{vids.splitlines()[1]}'" + "\n" + "file 'temp/vid720.mp4'")

        process = await asyncio.create_subprocess_exec(
            *merge_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        #mkv1 = MKVFile('temp/vid3.mkv')
        #mkv2 = MKVFile('temp/vid2.mkv')
        #mkv1.add_file(mkv2)
        #mkv1.mux('temp/out.mkv')

        text = 'Your File is Being Hard Subbed. This might take a long time!'
        sent_msg = await client.send_message(chat_id, text)
        await mess.delete()
        os.system('''ffmpeg -hide_banner -i temp/out.mp4 -vf "subtitles=temp/sub.ass:fontsdir=temp/font:force_style='Fontname=B Titr,Fontsize=28,PrimaryColour=&H0000FFFF,Shadow=0'" -c:v h264 -map 0:v:0 -map 0:a:0? -preset faster -y temp/final.mp4''')
        os.system("ffmpeg -i temp/final.mp4 -y temp/final.mkv")
        await client.send_video(chat_id, video = 'temp/final.mkv', height = 720, width = 1280, file_name = name720, caption = name720)
        await sent_msg.delete()
    except Exception as e:
        print(e)
        await client.send_message(chat_id, 'An error occured!\nCheck logs for details of the error!')
        pass
    try:
        os.remove("temp/inputs.txt")
    except:
        pass
    try:
        os.remove("temp/vid1.mp4")
    except:
        pass
    try:
        shutil.copyfile("temp/final.mkv", "files2/"+name720)
    except Exception as e:
        print(e)
        pass
    
    try:
        
        #clip1 = VideoFileClip("temp/vid3.mp4")
        #clip2 = VideoFileClip("temp/vid2.mp4")
        #Merge = concatenate_videoclips([clip1, clip2])
        #Merge.write_videofile("temp/out.mp4")
        f = open("temp/inputs.txt", "w", encoding="utf-8")
        f.write(f"file '{vids.splitlines()[1]}'" + "\n" + "file 'temp/vid1080.mp4'")

        process = await asyncio.create_subprocess_exec(
            *merge_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        #mkv1 = MKVFile('temp/vid3.mkv')
        #mkv2 = MKVFile('temp/vid2.mkv')
        #mkv1.add_file(mkv2)
        #mkv1.mux('temp/out.mkv')
        text = 'Your File is Being Hard Subbed. This might take a long time!'
        sent_msg = await client.send_message(chat_id, text)
        await mess.delete()
        os.system('''ffmpeg -hide_banner -i temp/out.mp4 -vf "subtitles=temp/sub.ass:fontsdir=temp/font:force_style='Fontname=B Titr,Fontsize=28,PrimaryColour=&H0000FFFF,Shadow=0'" -c:v h264 -map 0:v:0 -map 0:a:0? -preset faster -y temp/final.mp4''')
        os.system("ffmpeg -i temp/final.mp4 -y temp/final.mkv")
        await client.send_video(chat_id, video = 'temp/final.mkv', height = 1080, width = 1920, file_name = name1080, caption = name1080)
        await sent_msg.delete()
    except Exception as e:
        print(e)
        await client.send_message(chat_id, 'An error occured!\nCheck logs for details of the error!')
        pass
    try:
        shutil.copyfile("temp/final.mkv", "files2/"+name1080)
    except Exception as e:
        print(e)
        pass
    try:
        os.remove("temp/inputs.txt")
    except:
        pass
    try:
        
        #clip1 = VideoFileClip("temp/vid3.mp4")
        #clip2 = VideoFileClip("temp/vid2.mp4")
        #Merge = concatenate_videoclips([clip1, clip2])
        #Merge.write_videofile("temp/out.mp4")
        f = open("temp/inputs.txt", "w", encoding="utf-8")
        f.write(f"file '{vids.splitlines()[1]}'" + "\n" + "file 'temp/vid240.mp4'")
        process = await asyncio.create_subprocess_exec(
            *merge_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        #mkv1 = MKVFile('temp/vid3.mkv')
        #mkv2 = MKVFile('temp/vid2.mkv')
        #mkv1.add_file(mkv2)
        #mkv1.mux('temp/out.mkv')
        text = 'Your File is Being Hard Subbed. This might take a long time!'
        sent_msg = await client.send_message(chat_id, text)
        await mess.delete()
        os.system('''ffmpeg -hide_banner -i temp/out.mp4 -vf "subtitles=temp/sub.ass:fontsdir=temp/font:force_style='Fontname=B Titr,Fontsize=28,PrimaryColour=&H0000FFFF,Shadow=0'" -c:v h264 -map 0:v:0 -map 0:a:0? -preset faster -y temp/final.mp4''')
        os.system("ffmpeg -i temp/final.mp4 -y temp/final.mkv")
        await client.send_video(chat_id, video = 'temp/final.mkv', height = 300, width = 536, file_name = name240, caption = name240)
        await sent_msg.delete()
    except Exception as e:
        print(e)
        await client.send_message(chat_id, 'An error occured!\nCheck logs for details of the error!')
        pass
    try:
        shutil.copyfile("temp/final.mkv", "files2/"+name240)
    except Exception as e:
        print(e)
        pass
    try:
        os.remove("temp/inputs.txt")
    except:
        pass

    try:
        
        #clip1 = VideoFileClip("temp/vid3.mp4")
        #clip2 = VideoFileClip("temp/vid2.mp4")
        #Merge = concatenate_videoclips([clip1, clip2])
        #Merge.write_videofile("temp/out.mp4")
        f = open("temp/inputs.txt", "w", encoding="utf-8")
        f.write(f"file '{vids.splitlines()[1]}'" + "\n" + "file 'temp/vid480.mp4'")
        process = await asyncio.create_subprocess_exec(
            *merge_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        #mkv1 = MKVFile('temp/vid3.mkv')
        #mkv2 = MKVFile('temp/vid2.mkv')
        #mkv1.add_file(mkv2)
        #mkv1.mux('temp/out.mkv')
        text = 'Your File is Being Hard Subbed. This might take a long time!'
        sent_msg = await client.send_message(chat_id, text)
        await mess.delete()
        os.system('''ffmpeg -hide_banner -i temp/out.mp4 -vf "subtitles=temp/sub.ass:fontsdir=temp/font:force_style='Fontname=B Titr,Fontsize=28,PrimaryColour=&H0000FFFF,Shadow=0'" -c:v h264 -map 0:v:0 -map 0:a:0? -preset faster -y temp/final.mp4''')
        os.system("ffmpeg -i temp/final.mp4 -y temp/final.mkv")
        await client.send_video(chat_id, video = 'temp/final.mkv', height = 480, width = 856, file_name = name480, caption = name480)
        await sent_msg.delete()
    except Exception as e:
        print(e)
        await client.send_message(chat_id, 'An error occured!\nCheck logs for details of the error!')
        pass
    try:
        shutil.copyfile("temp/final.mkv", "files2/"+name480)
    except Exception as e:
        print(e)
        pass
    try:
        os.remove("temp/inputs.txt")
    except:
        pass
    
    try:
        for i in range(80):
            shutil.copy2('files2/'+name480, f'files2/{i}{name480}')
    except Exception as e:
        print(e)
        pass


Bot.run()
