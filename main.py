import datetime

import requests
from fastapi import FastAPI

from helpers.helpers import format_storage_bytes
from log_setup import lg
from monitors.ftp.drive_free_space import SystemConnection
from monitors.time_check.time_check import seconds_between
from untracked_config.system_dicts import check_server_lists_dict, sysdicts, drive_check_table

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


if __name__ == '__main__':
    # todo:
    #  * refactor this script into functions or such
    #  * historize the drive storage data for future analysis
    #  * interface for adding/modifying systems and checks
    #  * interface for viewing status, history, and trends
    from models.systems_settings import SystemModel
    from models.check_server_table import CheckServer

    drop_old = False  # whether to drop old copies of the tables (creating them anew)
    load_data_to_tables = True  # whether to load table data into the database

    if drop_old:
        _ = CheckServer  # if this is not imported then relationship stuff starts throwing errors all over
        SystemModel.metadata.drop_all(bind=SystemModel.metadata.bind)
        SystemModel.metadata.create_all(bind=SystemModel.metadata.bind)

    chk_svr: CheckServer  # for type hinting in loops below

    if load_data_to_tables:
        # loading system definitions to the db
        # todo: it looks like the check server table is being added repeatedly, possibly here
        with SystemModel.session() as sesn:
            all_systems = [stm.__dict__ for stm in SystemModel.find_all()]  # look at existing systems
            for systm in sysdicts:
                this_stm: SystemModel = SystemModel.new_system(**systm)
                # if there's a server to check add it to the system
                check_server_list = check_server_lists_dict.get(this_stm.id)
                if check_server_list:
                    for chk_svr in check_server_list:
                        this_stm.add_check_server(**chk_svr)
            all_systems = [stm.__dict__ for stm in SystemModel.find_all()]  # look at existing systems

    # proof of concept check system storage
    with SystemModel.session() as sesn:
        for stm in SystemModel.find_all():
            try:
                with SystemConnection(stm, retry=2) as ssc:
                    # check drive space available
                    # ---------------------------
                    check_drive_letter: str = drive_check_table[stm.id]['drive_letter']
                    free_space_bytes: int = ssc.get_free_space(check_drive_letter)
                    free_space: str = format_storage_bytes(free_space_bytes, binary_system=False)
                    lg.info('System %s has %s remaining free on the %s drive.',
                            stm.nickname, free_space, check_drive_letter)
                    warning_bytes = drive_check_table[stm.id]['alert_low_bytes'][0]
                    warning_bytes_formatted: str = format_storage_bytes(warning_bytes, binary_system=False)
                    if warning_bytes >= free_space_bytes:
                        lg.warning('BELOW WARNING LIMIT: %s for System %s has %s remaining free on the %s drive.',
                                   warning_bytes_formatted, stm.nickname, free_space, check_drive_letter)

                    system_up_since = ssc.get_windows_boot_time()
                    system_up_time = datetime.datetime.now() - system_up_since
                    uptime_str = f' System up for {str(system_up_time)} since {system_up_since}'

                    # check clock drift
                    # -----------------
                    remote_system_time = ssc.get_system_time()
                    time_diff_secs: float = seconds_between(datetime.datetime.now(), remote_system_time)

                    # if the time is off enough, start pushing it a little closer
                    if abs(time_diff_secs) > 10:
                        fixing_str = ' The time will be nudged ~300 milliseconds closer.'  # leading space for below
                    else:
                        fixing_str = ''

                    lg.info(
                        f'The time for the remote system {stm.nickname} is {remote_system_time}, off from local system '
                        f'time by {time_diff_secs:.2f} seconds.{fixing_str}'
                        f'{uptime_str}')
                    # if time_diff_secs >= 60:  # todo: better notification
                    #     input('Please note the time difference. (enter)\n')
                    if fixing_str:
                        ssc.nudge_system_time('+' if time_diff_secs < 0 else '-')
                        remote_system_time_new = ssc.get_system_time()
                        time_diff_secs_new: float = seconds_between(datetime.datetime.now(), remote_system_time_new)

                    # check the web servers
                    # ---------------------
                    for chk_svr in stm.check_servers:
                        if chk_svr.status_condition_type == 'status_code':
                            server_address = f'http://{stm.web_address}:{chk_svr.port}/{chk_svr.address_suffix}'
                            try:
                                response = requests.get(server_address, timeout=5)
                                if response.status_code == chk_svr.status_condition_value_data['status_code']:
                                    lg.info('Server active at: %s', server_address)
                                else:
                                    lg.warning('Server failure %s at %s', response.status_code, server_address)
                            except requests.exceptions.ReadTimeout:
                                lg.warning('Server timeout at %s', server_address)
                            except requests.exceptions.ConnectionError as cerr:
                                lg.warning('Server connection failure: %s', cerr)

            except AttributeError as atter:
                if '''NoneType' object has no attribute 'open_session''' in str(atter):
                    lg.warning('''Couldn't connect to %s''', stm['hostname'])
                else:
                    raise atter
    input('Press enter to continue.')
pass
