import os
from pathlib import Path

import lyricsgenius
from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest as unblock

from ...Config import Config
from ...core.session import catub
from ..utils.utils import runcmd
from .utube import name_dl, song_dl, video_dl

GENIUS = Config.GENIUS_API_TOKEN
ENV = bool(os.environ.get("ENV", False))


class LyricGenius:
    def __init__(self):
        if GENIUS:
            self.genius = lyricsgenius.Genius(GENIUS)

    def songs(self, title):
        songs = self.genius.search_songs(title)["hits"]
        return songs

    def song(self, title, artist=None):
        song_info = None
        try:
            if not artist:
                song_info = self.songs(title)[0]["result"]
            else:
                for song in self.songs(title):
                    if artist in song["result"]["primary_artist"]["name"]:
                        song_info = song["result"]
                        break
                if not song_info:
                    for song in self.songs(f"{title} by {artist}"):
                        if artist in song["result"]["primary_artist"]["name"]:
                            song_info = song["result"]
                            break
        except (AttributeError, IndexError):
            pass
        return song_info

    async def lyrics(self, title, artist=None, mode="lyrics"):
        lyrics = link = None
        if ENV:
            if not artist:
                song_info = self.song(title)["title"]
                song = self.genius.search_song(song_info)
                if song:
                    lyrics = song.lyrics
                    link = song.song_art_image_url
            else:
                song = self.genius.search_song(title, artist)
                if song:
                    lyrics = song.lyrics
                    link = song.song_art_image_url
        else:
            msg = f"{artist}-{title}" if artist else title
            chat = "@lyrics69bot"
            async with catub.conversation(chat) as conv:
                try:
                    flag = await conv.send_message("/start")
                except YouBlockedUserError:
                    await catub(unblock("lyrics69bot"))
                    flag = await conv.send_message("/start")
                await conv.get_response()
                await catub.send_read_acknowledge(conv.chat_id)
                await conv.send_message(f"/{mode} {msg}")
                if mode == "devloper":
                    link = (await conv.get_response()).text
                    await catub.send_read_acknowledge(conv.chat_id)
                lyrics = (await conv.get_response()).text
                await catub.send_read_acknowledge(conv.chat_id)
                await delete_by_client(catub, chat, flag)
        if mode == "devloper":
            return link, lyrics
        return lyrics


LyricsGen = LyricGenius()


async def delete_by_client(client, chat, from_message):
    itermsg = client.iter_messages(chat, min_id=from_message.id)
    msgs = [from_message.id]
    async for i in itermsg:
        msgs.append(i.id)
    await client.delete_messages(chat, msgs)
    await client.send_read_acknowledge(chat)


async def song_download(url, event, quality="128k", video=False, title=True):
    media_type = "Audio"
    media_ext = ["mp3", "mp4a"]
    media_cmd = song_dl.format(QUALITY=quality, video_link=url)
    name_cmd = name_dl.format(video_link=url)
    if video:
        media_type = "Video"
        media_ext = ["mp4", "mkv"]
        media_cmd = video_dl.format(video_link=url)

    try:
        stderr = (await runcmd(media_cmd))[1]
        media_name, stderr = (await runcmd(name_cmd))[:2]
        if stderr:
            return await event.edit(f"**Error ::** `{stderr}`")
        media_name = os.path.splitext(media_name)[0]
        media_file = Path(f"{media_name}.{media_ext[0]}")
    except:
        pass
    if not os.path.exists(media_file):
        media_file = Path(f"{media_name}.{media_ext[1]}")
    elif not os.path.exists(media_file):
        return await event.edit(
            f"__Sorry!.. I'm unable to find your requested {media_type}.__"
        )
    await event.edit(f"__Uploading requested {media_type}...__")
    media_thumb = Path(f"{media_name}.jpg")
    if not os.path.exists(media_thumb):
        media_thumb = Path(f"{media_name}.webp")
    elif not os.path.exists(media_thumb):
        media_thumb = None
    if title:
        media_title = media_name.replace("./temp/", "").replace("_", "|")
        return media_file, media_thumb, media_title
    return media_file, media_thumb
