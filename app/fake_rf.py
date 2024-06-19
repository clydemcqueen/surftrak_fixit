#! /usr/bin/env python3

"""Send DISTANCE_SENSOR messages to mavlink2rest for bench testing"""

import argparse
import random
import time

import mav_client


def main(args):
    print(args)
    # Get a mav client to access mavlink2rest, but do not open a websocket
    mav = mav_client.MavClient(args.mavlink2rest_url)

    msg = None
    while msg is None:
        time.sleep(1)
        msg = mav.get_template('DISTANCE_SENSOR')
    print(msg)

    msg['message']['min_distance'] = 22
    msg['message']['max_distance'] = 4444
    msg['message']['mavtype'] = {'type': 'MAV_DISTANCE_SENSOR_ULTRASOUND'}
    msg['message']['id'] = 9
    msg['message']['orientation'] = {'type': 'MAV_SENSOR_ROTATION_PITCH_270'}
    msg['message']['covariance'] = 255
    msg['message']['horizontal_fov'] = 0.52
    msg['message']['vertical_fov'] = 0.52
    msg['message']['signal_quality'] = 95

    start_time = time.time()

    while True:
        msg['message']['time_boot_ms'] = int((time.time() - start_time) * 1000)

        if args.ping:
            msg['header']['system_id'] = 1
            msg['header']['component_id'] = 194
            msg['message']['current_distance'] = 500 + int(random.random() * 10)
            mav.send_msg('fake ping', msg)

        if args.wl_dvl:
            msg['header']['system_id'] = 255
            msg['header']['component_id'] = 0
            msg['message']['current_distance'] = 600 + int(random.random() * 10)
            mav.send_msg('fake wl dvl', msg)

        time.sleep(0.3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--mavlink2rest_url', type=str, default='http://localhost:8088/v1',
                        help='mavlink2rest URL')
    parser.add_argument('--ping', default=None, action='store_true',
                        help='emulate Ping sonar')
    parser.add_argument('--wl-dvl', default=None, action='store_true',
                        help='emulate WL DVL')
    parser.add_argument('--sq', type=str, default=95,
                        help='signal quality')
    main(parser.parse_args())
