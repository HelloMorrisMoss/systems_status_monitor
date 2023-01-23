from pprint import pprint

from fastapi import FastAPI

from helpers.helpers import format_storage_bytes
from log_setup import lg
from monitors.ftp.drive_free_space import SSH_Connection
from untracked_config.system_dicts import sysdicts

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


if __name__ == '__main__':
    from models.systems_settings import SystemModel

    load = True

    if load:
        # loading system defitions to the db
        with SystemModel.session() as sesn:
            all_systems = [stm.__dict__ for stm in SystemModel.find_all()]  # look at existing systems
            pprint(all_systems)
            for systm in sysdicts:
                SystemModel.new_system(**systm)
            all_systems = [stm.__dict__ for stm in SystemModel.find_all()]  # look at existing systems
            pprint(all_systems)

    # proof of concept check system storage
    with SystemModel.session() as sesn:
        all_systems = [stm.__dict__ for stm in SystemModel.find_all()]
        for stm in all_systems:
            # use the static ip if we have it, otherwise use the hostname
            hostname = stm['hostname'] if not stm['static_ip'] else stm['static_ip']
            username = stm['username']
            password = stm['password']
            settings_dict = dict(hostname=hostname, username=username, password=password)
            free_space = SSH_Connection(settings_dict).get_free_space()
            lg.info('System %s has %s remaining free on the C drive.',
                    stm['nickname'],
                    format_storage_bytes(free_space))
pass
