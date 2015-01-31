# SwampDragon python client

Communicate with SwampDragon through python.


## Examples

    def on_channel_message(channel, message):
        # Only care if the channel is "test"
        if channel == 'test':
            output = '{} says: {}'.format(message.get('name'), message.get('message'))
            print(output)

    def on_subscribed(context, message):
        print('-subscribed-')
        
    url = 'ws://localhost:9999/data'
    client = DragonClient(url, on_channel_message=on_channel_message)
    client.connect()
    
    # Subscribe to the chat router
    client.call_router('subscribe', 'chat-route', callback=on_subscribed, channel='test')
    
    # Send a message as Veronica saying "Hello world"
    client.call_router('chat', 'chat-route', callback=on_chat, name='Veronica', message='Hello world')
    

## Client functions

`client.connect` connects to the server and starts listening to incoming data
`client.disconnect` disconnects from the server

`client.call_router` takes the following args:

*  verb
*  route
*  callback=None
*  **kwargs

The `callback` is any function that takes two arguments: `context` and `message`
