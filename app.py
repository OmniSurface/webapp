from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from threading import Thread, Lock
import asyncio
from bleak import BleakClient, BleakError, BleakScanner
import time
import logging

# Start the monitoring in a separate thread
client = None
current_task = None  #ble_read task
data_lock = Lock()
connect_lock = asyncio.Lock()

app = Flask(__name__) # create an instance of the Flask class
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)
app.logger.setLevel(logging.ERROR)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

address = "dc:54:75:d7:bc:00"  # Device address
char_uuid = "bff7f0c9-5fbf-4b63-8d83-b8e077176fbe"  # Characteristic UUID to read from

ble_data = 0

async def handle_reconnect(client):
    global current_task
    # if current_task and not current_task.done():
    #     current_task.cancel()
    if current_task:
        current_task.cancel()
    await asyncio.sleep(2)  # Short delay before attempting to reconnect
    print("Attempting to reconnect...")
    current_task = asyncio.create_task(ble_read())

# Define the disconnected callback
def disconnected_callback(client):
    # global current_task

    print("Disconnected, attempting to reconnect...")
    # Schedule the handle_reconnect coroutine to be run on the event loop
    # if not(current_task and not current_task.done()):
    asyncio.create_task(handle_reconnect(client))

    # This ensures disconnected_callback does not directly call ble_read(),
    # but schedules a reconnect attempt, allowing for cleanup.
    # asyncio.get_event_loop().call_later(5, asyncio.create_task, ble_read())

def update_ble_data(data):
    print(f'Updating ble data: {data}')
    socketio.emit('bledata', data)

# a callback function that gets called every time the specified characteristic (identified by char_uuid) is updated
async def notification_handler(sender, data):
    global ble_data
    global clearTogglePushed
    global clearTogglePushedTime

    with data_lock:
        decoded_value = data.decode('utf-8').strip()
        ble_data = decoded_value
        update_ble_data(ble_data)

async def ble_read():
    global client, current_task
    # client = None  # Initialize client here to ensure it's in the function's scope

    while True:
        try:
            async with connect_lock:
                if (client is None) or (not client.is_connected):
                    client = BleakClient(address, disconnected_callback=disconnected_callback)
                    await client.connect()
                    print(f"Connected to {address}")
                    await client.start_notify(char_uuid, notification_handler)

            while client.is_connected:
                await asyncio.sleep(1)

        except (BleakError, Exception) as e:
            print(f"BLE connection error in ble_read(): {e}")

        finally:
            if client and client.is_connected:
                await client.disconnect()
            client = None
            await asyncio.sleep(4)  # Retry delay



def start_ble_read():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    current_task = loop.run_until_complete(ble_read())



@app.route('/') # use the route() decorator to tell Flask what URL should trigger our function
def index():
    return render_template('index.html')


@socketio.on('connect')
def test_connect():
    socketio.emit('welcome', {'message': 'Welcome!'})
    print('Client connected')

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')




if __name__ == '__main__':
    thread = Thread(target=start_ble_read)
    thread.start()
    socketio.run(app, debug=True) # run the application