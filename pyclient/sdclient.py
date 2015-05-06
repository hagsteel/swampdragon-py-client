import random
import string
import threading
import json
import websocket


channels = {}


def message_to_json(data):
    if isinstance(data, dict):
        return data
    try:
        data = json.loads(data)
        # Channel messages come back as escaped strings and needs to be loaded as json again (it's an odd one)
        if not isinstance(data, dict):
            data = json.loads(data)
        return data
    except:
        return json.dumps({'message': data})


class DragonClient(object):
    def __init__(self, url, on_channel_message=None, on_open=None, on_exception=None):
        self.thread = None
        if url[-1] != '/':
            url = '{}/'.format(url)
        self.url = '{}{}/{}/websocket'.format(url, self._rand_int(), self._rand_string())
        self.call_queue = []
        self.is_connected = False
        self.callbacks = {}
        self.callback_index = 0
        self.on_channel_message = on_channel_message
        self.on_exception = on_exception

    def _rand_int(self):
        return random.randint(0, 1000)

    def _rand_string(self):
        return ''.join(random.choice(string.ascii_lowercase) for _ in range(10))

    def run(self):
        self.thread = threading.Thread(target=self.ws.run_forever)
        self.thread.start()

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open
        )
        self.run()

    def disconnect(self):
        self.ws.close()

    def on_message(self, ws, message):
        if message[0:2] != 'a[':  # This is not a message for the client
            return

        message = message_to_json(message[2:-1])
        context = message.get('context')
        data = message.get('data')

        # Channel setup
        channel_data = message.get('channel_data')
        if channel_data:
            remote_channels = channel_data.get('remote_channels') or []
            local_channel = channel_data['local_channel']
            for rc in remote_channels:
                channels[rc] = local_channel

        if context:
            callback_name = context.get('client_callback_name')
            if callback_name:
                cb_key = int(callback_name[3:])
                callback = self.callbacks.pop(cb_key, None)
                if callback:
                    callback(context, data)
        elif 'channel' in message and self.on_channel_message:
            self.on_channel_message(channels[message['channel']], message)

    def on_error(self, ws, error):
        if self.on_exception:
            self.on_exception(error)

    def on_close(self, ws):
        self.is_connected = False

    def on_open(self, ws):
        self.is_connected = True
        for f in self.call_queue:
            self._send(f)

    def _send(self, message):
        self.ws.send(message)

    def call_router(self, verb, route, callback=None, **kwargs):
        self.callback_index += 1
        callback_id = self.callback_index
        self.callbacks[callback_id] = callback
        message = json.dumps({
            'verb': verb,
            'route': route,
            'args': kwargs,
            'callbackname': 'cb_{}'.format(callback_id)
        })
        if self.is_connected:
            self._send(message)
        else:
            self.call_queue.append(message)
