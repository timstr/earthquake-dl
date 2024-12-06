#!/usr/bin/env python3

import math
import numpy as np
import obspy
import os
import requests
import scipy.io.wavfile as wf
import shutil
import sys
import tempfile


def main():
    default_network = "IU"
    default_station_code = "ANMO"
    default_start_time = "2010-02-27T06:30:00"
    default_end_time = "2010-02-27T10:30:00"

    network = input(f"Enter network [{default_network}]: ").strip() or default_network
    station_code = (
        input(f"Enter station code [{default_station_code}]: ").strip()
        or default_station_code
    )
    start_time = (
        input(f"Enter start time [{default_start_time}]: ").strip()
        or default_start_time
    )
    end_time = (
        input(f"Enter end time [{default_end_time}]: ").strip() or default_end_time
    )

    base_url = "https://service.iris.edu/fdsnws/dataselect/1/query"

    query_string_items = [
        ("net", network),
        ("sta", station_code),
        ("loc", "*"),
        ("cha", "*"),
        ("start", start_time),
        ("end", end_time),
        ("quality", "B"),
        ("format", "miniseed"),
    ]

    query_string = "&".join([f"{k}={v}" for k, v in query_string_items])

    full_url = f"{base_url}?{query_string}"

    print(f"Making a request to:\n    {full_url}")

    response = requests.get(full_url)

    if response.status_code == 204:
        print("The server did not find any data")
        return
    elif response.status_code != 200:
        print("The server did not like that request.")
        return

    print(f"Received {len(response.content)} bytes")

    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, "data.seed")

    with open(temp_file_path, "wb") as f:
        f.write(response.content)

    output_dir = f"{station_code}_{start_time}_to_{end_time}"

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    streams = obspy.read(temp_file_path)

    num_channel_digits = int(math.ceil(math.log10(len(streams))))

    for i, stream in enumerate(streams):
        channel_name = stream.stats.channel
        file_name = f"{str(i).zfill(num_channel_digits)}_{channel_name}.wav"
        file_path = os.path.join(output_dir, file_name)
        print(f"Saving channel {channel_name} to {file_path}")
        arr = stream.data
        print(f"shape = {arr.shape}")
        # normalize and make quiet
        arr = arr - np.mean(arr)
        arr = arr * (0.2 / np.max(np.abs(arr)))
        wf.write(file_path, 44100, arr)

    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()
