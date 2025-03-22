@click.command()
@click.option('--days', default=0, help='Last X days which you want to list videos for.')
@click.option('--date', default='', help='Specific date in YYYY-MM-DD format for which you want to list videos. Takes precedence over --days.')
def list_videos(days, date):
    """Lists videos for the last X days or for a specific date."""
    get_config() # Checks if logged in
    endpoint = '/api/v2/common/getDeviceListByPage'
    content = '{"deviceTypeList":["SMART.IPCAMERA"],"index":0,"limit":20}'
    devs = probe_endpoint_post(content, endpoint)
    
    # Calculate start and end time based on input parameters
    if date:
        # If a specific date is provided, set start and end time to that day
        try:
            # Parse the provided date
            specific_date = datetime.datetime.strptime(date, '%Y-%m-%d')
            # Set start time to 00:00:00 of the specified date
            start_time = specific_date.strftime('%Y-%m-%d 00:00:00')
            # Set end time to 23:59:59 of the specified date
            next_day = specific_date + datetime.timedelta(days=1)
            end_time = next_day.strftime('%Y-%m-%d 00:00:00')
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD format.")
            return
    else:
        # Use the original days-based calculation if no specific date is provided
        if days <= 0:
            days = 1  # Default to 1 day if not specified or invalid
        
        end_unixtime = time.time() + 86400
        start_unixtime = end_unixtime - (days + 1) * 86400
        end_time = datetime.datetime.utcfromtimestamp(end_unixtime).strftime('%Y-%m-%d 00:00:00')
        start_time = datetime.datetime.utcfromtimestamp(start_unixtime).strftime('%Y-%m-%d 00:00:00')

    print(f"Listing videos from {start_time} to {end_time}")
    
    endpoint = '/v2/videos/list'
    for dev in devs['deviceList']:
        params = 'deviceId=' + dev['deviceId'] + '&page=0&pageSize=3000&order=desc&startTime=' + start_time + '&endTime=' + end_time
        videos = probe_endpoint_get(params, endpoint)
        print('\nFound ' + str(videos['total']) + ' videos for ' + dev['alias'] + ':')
        if 'index' in videos:
            for video in videos['index']:
                print(video['eventLocalTime'], end = ", ")
                #print(video['video'][0]['uri']) # This will print URLs to the videos if you want to download them using another tool, but don't forget to get the AES key from video['video'][0]['decryptionInfo']['key']
        if videos['total'] > 0: print('')


@click.command()
@click.option('--days', default=0, help='Last X days which you want to download videos for.')
@click.option('--date', default='', help='Specific date in YYYY-MM-DD format for which you want to download videos. Takes precedence over --days.')
@click.option('--path', default="~/", prompt="Path", help='Path where you want your videos to be downloaded. It will create directories based on dates.')
@click.option('--overwrite', default=0, prompt="Overwrite", help='Overwrite any files using the same name in the same location.')
def download_videos(days, date, path, overwrite):
    """Downloads videos for the last X days or for a specific date to path."""
    get_config() # Checks if logged in
    
    path = path if path[-1] == '/' else path + '/'
    path = os.path.expanduser(path)
    
    endpoint = '/api/v2/common/getDeviceListByPage'
    content = '{"deviceTypeList":["SMART.IPCAMERA"],"index":0,"limit":20}'
    devs = probe_endpoint_post(content, endpoint)
    
    # Calculate start and end time based on input parameters
    if date:
        # If a specific date is provided, set start and end time to that day
        try:
            # Parse the provided date
            specific_date = datetime.datetime.strptime(date, '%Y-%m-%d')
            # Set start time to 00:00:00 of the specified date
            start_time = specific_date.strftime('%Y-%m-%d 00:00:00')
            # Set end time to 23:59:59 of the specified date
            next_day = specific_date + datetime.timedelta(days=1)
            end_time = next_day.strftime('%Y-%m-%d 00:00:00')
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD format.")
            return
    else:
        # Use the original days-based calculation if no specific date is provided
        if days <= 0:
            days = 1  # Default to 1 day if not specified or invalid
        
        end_unixtime = time.time() + 86400
        start_unixtime = end_unixtime - (days + 1) * 86400
        end_time = datetime.datetime.utcfromtimestamp(end_unixtime).strftime('%Y-%m-%d 00:00:00')
        start_time = datetime.datetime.utcfromtimestamp(start_unixtime).strftime('%Y-%m-%d 00:00:00')

    print(f"Downloading videos from {start_time} to {end_time}")
    
    result = []
    endpoint = '/v2/videos/list'
    for dev in devs['deviceList']:
        params = 'deviceId=' + dev['deviceId'] + '&page=0&pageSize=3000&order=desc&startTime=' + start_time + '&endTime=' + end_time
        videos = probe_endpoint_get(params, endpoint)
        print('\nFound ' + str(videos['total']) + ' videos for ' + dev['alias'] + ':')
        if 'index' in videos:
            for video in videos['index']:
                url = video['video'][0]['uri']
                key_b64 = False

                # Check if the video is encrypted and get the key
                if 'encryptionMethod' in video['video'][0]:
                    method = video['video'][0]['encryptionMethod']
                    if method != "AES-128-CBC":
                        print(f"Unsupported encryption method: {method}. Quitting...")
                        print("Create an issue here: https://github.com/dimme/tapo-cli/issues")
                        exit(1)

                    key_b64 = video['video'][0]['decryptionInfo']['key']
                
                file_path = path + dev['alias'] + '/' + datetime.datetime.strptime(video['eventLocalTime'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d') + '/'
                file_name = video['eventLocalTime'].replace(':','-') + '.mp4'
                if os.path.exists(file_path + file_name) and overwrite == 0:
                    print('Already exists ' + file_path + file_name)    
                    result.append({'file': file_path + file_name, 'device': dev['alias'], 'new_video': False, 'video': video})
                else:
                    print('Downloading to ' + file_path + file_name)
                    download(url, key_b64, file_path, file_name)
                    result.append({'file': file_path + file_name, 'device': dev['alias'], 'new_video': True, 'video': video})
    return result

# Aggiorna i comandi nel CLI
tapo.add_command(login, 'login')
tapo.add_command(account_info, 'list-account-info')
tapo.add_command(devices_limit, 'list-devices-limit')
tapo.add_command(devices_info, 'list-devices-info')
tapo.add_command(devices, 'list-devices')
tapo.add_command(service_urls, 'list-service-urls')
tapo.add_command(notifications, 'list-notifications')
tapo.add_command(subscriptions, 'list-subscriptions')
tapo.add_command(mfa_status, 'list-mfa-status')
tapo.add_command(list_videos, 'list-videos')
tapo.add_command(download_videos, 'download-videos')
