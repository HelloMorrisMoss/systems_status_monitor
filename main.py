import datetime

from fastapi import FastAPI

from helpers.helpers import format_storage_bytes
from log_setup import lg
from monitors.ftp.drive_free_space import SSH_Connection
from monitors.time_check.time_check import seconds_between
from untracked_config.system_dicts import check_server_table, sysdicts, drive_check_table

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


if __name__ == '__main__':
    from models.systems_settings import SystemModel
    from models.check_server_table import CheckServer

    drop_old = False  # whether to drop old copies of the tables
    load_data_to_tables = True  # whether to load table data into the database

    if drop_old:
        _ = CheckServer  # if this is not imported then relationship stuff starts throwing errors all over
        SystemModel.metadata.drop_all(bind=SystemModel.metadata.bind)
        SystemModel.metadata.create_all(bind=SystemModel.metadata.bind)

    if load_data_to_tables:
        # loading system definitions to the db
        with SystemModel.session() as sesn:
            all_systems = [stm.__dict__ for stm in SystemModel.find_all()]  # look at existing systems
            for systm in sysdicts:
                this_stm: SystemModel = SystemModel.new_system(**systm)
                # if there's a server to check add it to the system
                check_server_dict = check_server_table.get(this_stm.id)
                if check_server_dict:
                    this_stm.add_check_server(**check_server_dict)
            all_systems = [stm.__dict__ for stm in SystemModel.find_all()]  # look at existing systems

    # proof of concept check system storage
    with SystemModel.session() as sesn:
        all_systems = [stm.__dict__ for stm in SystemModel.find_all()]
        for stm in all_systems:
            # use the static ip if we have it, otherwise use the hostname
            hostname = stm['hostname'] if not stm['static_ip'] else stm['static_ip']
            username = stm['username']
            password = stm['password']
            settings_dict = dict(hostname=hostname, username=username, password=password)
            try:
                ssc = SSH_Connection(settings_dict, retry=2)
                free_space = ssc.get_free_space()
                lg.info('System %s has %s remaining free on the C drive.',
                        stm['nickname'],
                        format_storage_bytes(free_space))
                remote_system_time = ssc.get_system_time()
                time_diff_secs: float = seconds_between(datetime.datetime.now(), remote_system_time)

                # if the time is off enough, start pushing it closer
                if abs(time_diff_secs) > 10:
                    fixing_str = ' The time will be nudged ~300 milliseconds closer.'
                else:
                    fixing_str = ''
                    lg.info(f'The remote system time is {remote_system_time}, off from local system time by '
                            f'{time_diff_secs:.2f} seconds.{fixing_str}')
                if fixing_str:
                    ssc.nudge_system_time('+' if time_diff_secs > 10 else '-')
            except AttributeError as atter:
                if '''NoneType' object has no attribute 'open_session''' in str(atter):
                    lg.warning('''Couldn't connect to %s''', stm['hostname'])
                else:
                    raise atter
    input('Press enter to continue.')
pass
