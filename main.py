from fastapi import FastAPI

from helpers.helpers import format_storage_bytes
from monitors.ftp.drive_free_space import SSH_Connection

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


if __name__ == '__main__':
    set_dict = dict(hostname='10.155.0.84',
                    username='username',
                    password='password')
    ssc = SSH_Connection(set_dict)
    fs = ssc.get_free_space()
    print(format_storage_bytes(fs))
