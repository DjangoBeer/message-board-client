from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import BooleanProperty, ObjectProperty
from kivy.network.urlrequest import UrlRequest
from kivy.uix.screenmanager import SlideTransition
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup

import json
import urllib

import os

Builder.load_file('./client.kv')

class MenuScreen(Screen):
    pass


class SettingsScreen(Screen):
    pass


class CameraScreen(Screen):
    def make_photo(self, camera):
        camera.texture.save('snapshot.jpg')
        sm.current = 'messages'


class MessageScreen(Screen):
    def send_message(self, text):
        if text.strip():
            self.pb = None
            def loading(request, current_size, total_size):
                self.pb.value += current_size
                if self.pb.value >= total_size:
                    self.popup.dismiss()

            with open(os.path.join(App.get_running_app().user_data_dir, 'usr_auth'), 'rb') as f:
                auth_data = json.load(f)
                headers = {
                    'Content-type': 'application/x-www-form-urlencoded',
                    'Authorization': 'Token {0}'.format(auth_data['token'])
                    }
                data_to_send = {'message': text}
                if os.path.exists('snapshot.jpg'):
                    data_to_send['photo'] = open('snapshot.jpg', 'rb').read()
                params = urllib.urlencode(data_to_send)
                req = UrlRequest('http://localhost:8000/messages/', req_body=params,
                req_headers=headers, timeout=10, on_progress=loading)
                self.pb = ProgressBar() #100
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
                    with open(os.path.join(App.get_running_app().user_data_dir, 'usr_auth'), 'wb') as f:
                        json.dump(result, f)
                        sm.current = 'messages'
            params = json.dumps({'username': user, 'password': pwd})
            headers = {'Content-type': 'application/json',
                      'Accept': 'application/json'}
            req = UrlRequest('http://localhost:8000/api-token-auth/', req_body=params,
                    req_headers=headers, timeout=10, on_success=save_auth, on_progress=loading)
            self.pb = ProgressBar() #100
            self.popup = Popup(title='Get token from the server...', content=self.pb, size_hint=(0.7, 0.3))
            self.popup.open()



# Create the screen manager
sm = ScreenManager(transition=SlideTransition())
sm.add_widget(MenuScreen(name='menu'))
#sm.add_widget(SettingsScreen(name='settings'))
sm.add_widget(MessageScreen(name='messages'))
sm.add_widget(CameraScreen(name='photo'))
sm.add_widget(LoginScreen(name='login'))
#sm.add_widget(LoginScreen(name='register'))


class ClientApp(App):

    logged_in = BooleanProperty(False)

    def build(self):
        self.logged_in = os.path.exists(os.path.join(self.user_data_dir, "usr_auth"))
        self.title = 'Message Board'
        if self.logged_in:
            sm.current = 'messages'
        return sm

if __name__ == '__main__':
    ClientApp().run()
