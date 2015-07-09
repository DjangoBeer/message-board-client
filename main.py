from kivy.app import App
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.lang import Builder
from kivy.network.urlrequest import UrlRequest
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.uix.camera import Camera
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.storage.jsonstore import JsonStore

from plyer import camera
import base64
import json
import urllib
import os

__version__ = '1.0.0'

Builder.load_file('./client.kv')

default_config = {'host': 'localhost', 'port': 8000}

CONFIG_PATH = 'client_config'
USR_AUTH = 'usr_auth'
IMG_PATH = '/storage/sdcard0/snapshot.jpg'

def get_app():
    return App.get_running_app()

def get_app_path():
    return get_app().user_data_dir

def get_user_path():
    return os.path.join(get_app_path(), USR_AUTH)

def get_config_path():
    return os.path.join(get_app_path(), CONFIG_PATH)


class MenuScreen(Screen):
    def goto(self):
        if not len(get_app().user_store):
            if not len(get_app().config_store):
                get_app().config_store.put('config', **default_config)
            sm.current = 'login'
        else:
            sm.current = 'messages'


class SettingsScreen(Screen):
    def save_config(self, host, port):
        if host and port:
            get_app().config_store.put('config', host=host, port=port)


class CameraScreen(Screen):

    def make_photo(self):
        try:
            self.add_widget(CameraLayout())
        except:
            cam = Camera(resolution=(640, 480), play=True)
            if cam.texture:
                cam.texture.save()
            sm.current = 'messages'


class MessageScreen(Screen):
    def send_message(self, text):
        if text.strip():
            self.pb = None
            def loading(request, current_size, total_size):
                self.pb.value += current_size
                if self.pb.value >= total_size:
                    self.popup.dismiss()
                    if os.path.exists(IMG_PATH):
                        os.remove(IMG_PATH)

            token = get_app().user_store.get('auth')['token']
            headers = {
                'Content-type': 'application/x-www-form-urlencoded',
                'Authorization': 'Token {0}'.format(token)
                }
            data_to_send = {'message': text}
            if os.path.exists(IMG_PATH):
                data_to_send['photo'] = base64.b64encode(open(IMG_PATH, 'rb').read())
            params = urllib.urlencode(data_to_send)
            host = get_app().config_store.get('config')['host']
            port = get_app().config_store.get('config')['port']
            req = UrlRequest('http://{0}:{1}/messages/'.format(host, port), req_body=params,
            req_headers=headers, timeout=10, on_progress=loading)
            self.pb = ProgressBar()
            self.popup = Popup(title='Sending message', content=self.pb, size_hint=(0.7, 0.3))
            self.popup.open()


class LoginScreen(Screen):
    def login(self, user, pwd):
        if user.strip() and pwd.strip():
            def loading(request, current_size, total_size):
                self.pb.value += current_size
                if self.pb.value >= total_size:
                    self.popup.dismiss()

            def save_auth(req, result):
                if 'token' in result:
                    get_app().user_store.put('auth', token=result['token'])
                    sm.current = 'messages'

            params = json.dumps({'username': user, 'password': pwd})
            headers = {'Content-type': 'application/json',
                      'Accept': 'application/json'}
            host = get_app().config_store.get('config')['host']
            port = get_app().config_store.get('config')['port']
            req = UrlRequest('http://{0}:{1}/api-token-auth/'.format(host, port), req_body=params,
                    req_headers=headers, timeout=10, on_success=save_auth, on_progress=loading)
            self.pb = ProgressBar()
            self.popup = Popup(title='Get token from the server...', content=self.pb, size_hint=(0.7, 0.3))
            self.popup.open()



# Create the screen manager
sm = ScreenManager(transition=SlideTransition())
sm.add_widget(MenuScreen(name='menu'))
sm.add_widget(SettingsScreen(name='settings'))
sm.add_widget(MessageScreen(name='messages'))
sm.add_widget(CameraScreen(name='photo'))
sm.add_widget(LoginScreen(name='login'))
#sm.add_widget(LoginScreen(name='register'))


class CameraLayout(FloatLayout):
    def __init__(self, **kwargs):
        super(CameraLayout, self).__init__(**kwargs)
        self.lblCam = Label(text="Click to take a picture!")
        self.add_widget(self.lblCam)

    def on_touch_down(self, e):
        try:
            camera.take_picture(IMG_PATH, self.done)
        except:
            pass

    def done(self, e):
        sm.current = 'messages'


class ClientApp(App):

    def build(self):
        self.user_store = JsonStore(get_user_path())
        self.config_store = JsonStore(get_config_path())
        self.title = 'Message Board'
        return sm

    def on_pause(self):
        return True

    def on_resume(self):
        pass

if __name__ == '__main__':
    ClientApp().run()
