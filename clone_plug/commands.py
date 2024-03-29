import os
import logging
import random
import asyncio
from Script import script
from pyrogram import Client, filters, enums
from tobot import tobot
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id
from database.users_chats_db import db
from info import CHANNELS, ADMINS, AUTH_CHANNEL, LOG_CHANNEL, BATCH_FILE_CAPTION, CUSTOM_FILE_CAPTION
from utils import get_settings, get_size, is_subscribed, save_group_settings, temp
from database.connections_mdb import active_connection
from clone_plug.pm_filter import QUERY
from plugins.clone import clonedme
from plugins.clone import send_clone_file
import re
import json
import base64
logger = logging.getLogger(__name__)

BATCH_FILES = {}

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton(' ᴄʟᴏꜱᴇ ᴛʜɪꜱ ', callback_data='close_data')
       ]]
        reply_markup = InlineKeyboardMarkup(buttons)     
        await message.reply_text(
            text=script.START_TXT.format(clonedme.U_NAME, clonedme.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML 
        )
        return
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
        
    if pre == "clone_pmfilter":
        key = file_id
        search = QUERY.get(key)
        files, offset, total_results = await get_search_results(query=search.lower(), offset=0, filter=True, max_results=6)
        ms = await message.reply_text(f"Searching For {search}")
        base_str = f"<b>Hey: {message.from_user.mention}\n\nYour Search Result is [{search}]</b>"
        btn = []
        if offset != "":
            key = f"{message.chat.id}-{message.id}"
            BUTTONS[key] = search
            req = message.from_user.id if message.from_user else 0
            btn.append(
                [InlineKeyboardButton(text=f"📃 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
                 InlineKeyboardButton(text="NEXT ▶️", callback_data=f"pmnext_{req}_{key}_{offset}")]
            )
        else:
            btn.append(
                [InlineKeyboardButton(text="📃 1/1", callback_data="pages")]
            )
        for file in files:
            me = await client.get_me()
            base_str += f"\n\n<a href='https://t.me/{me.username}?start=file_{file.file_id}'>⏩ [{get_size(file.file_size)}] {file.file_name}</a>"
        return await ms.edit(base_str, reply_markup=InlineKeyboardMarkup(btn))

    files_ = await get_file_details(file_id)           
    if not files_:
        pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        try:
            msg = await client.send_cached_media(
                chat_id=LOG_CHANNEL,
                file_id=file_id,
                protect_content=True if pre == 'filep' else False,
                )
            from_chat = msg.chat.id 
            mg_id = msg.id
            await client.copy_message(msg.from_user.id,from_chat,mg_id)  
            filetype = msg.media
            file = getattr(msg, filetype)
            title = file.file_name
            size=get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    return  
            await msg.edit_caption(f_caption)
            return
        except:
            pass
        return await message.reply('No such file exist.')
    files = files_[0]
    title = files.file_name
    size=get_size(files.file_size)
    f_caption=files.caption
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except Exception as e:
            logger.exception(e)
            f_caption=f_caption
    if f_caption is None:
        f_caption = f"{files.file_name}"
    f_caption = "new name"
    msg = await send_clone_file(tobot, file_id, f_caption)
    user = message.from_user.id
    chat = msg.chat.id
    file = msg.id
    await client.copy_message(user,chat,file)
        
    
    
