import tekore as tk
from pprint import pprint
import asyncio
from dotenv import load_dotenv
import os

from song import Song

class Spotify:
    """
    Interface to the Spotify API
    """
    token_file = "spotify_token.tok"

    def __init__(self, now_playing: Song):
        load_dotenv()
        self.config = tk.config_from_environment()
        self.creds = tk.Credentials(*self.config)
        self.auth = tk.UserAuth(self.creds, tk.scope.user_read_currently_playing)
        self.client = tk.Spotify(asynchronous=True)
        self.now_playing = now_playing
        self.retrieve_token()

    def auth_url(self):
        """
        Returns the URL which can be used to acquire an authentication token for the current user.
        :return:
        """
        return self.auth.url

    def update_token(self, code, state):
        self.client.token = self.auth.request_token(code, state)
        with open(self.token_file, "w") as f:
            f.write(self.client.token.refresh_token)

    def retrieve_token(self):
        if os.path.isfile(self.token_file):
            with open(self.token_file, "r") as f:
                tok = f.read()
                self.client.token = self.creds.refresh_user_token(tok)

    async def update_pause_state(self):
        while 1:
            if self.client.token:
                if self.client.token.is_expiring:
                    self.client.token = self.creds.refresh(self.client.token)
                current_track_data = await self.client.playback_currently_playing()
                if current_track_data:
                    self.now_playing.paused = not current_track_data.is_playing
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(1)

    async def update_now_playing(self):
        while 1:
            if self.client.token:
                if self.client.token.is_expiring:
                    self.client.token = self.creds.refresh(self.client.token)
                current_track_data = await self.client.playback_currently_playing()
                if current_track_data and current_track_data.item.id != self.now_playing.spotify_id:
                    await self.now_playing.update(
                        spotify_id=current_track_data.item.id,
                        title=current_track_data.item.name,
                        artists=[artist.name for artist in current_track_data.item.artists],
                        album=current_track_data.item.album.name,
                        album_art=max(current_track_data.item.album.images, key=lambda image: image.height).url,
                        lyrics=""
                    )
                await asyncio.sleep(3)
            else:
                print(f"No token found. Please authenticate at {self.auth_url()}")
                await asyncio.sleep(1)