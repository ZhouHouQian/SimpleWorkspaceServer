#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : 2024-10-12 14:17:32
# @Author  : houqianzhou
# @Desc    : 服务启动入口
import sys
import os
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import config

app = FastAPI()

security = HTTPBasic()

async def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    if config.USER == credentials.username and config.PASSWORD == credentials.password:
        return credentials.username
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Basic"},
    )

@app.get("/Files")
async def get_file(path=None, user: str = Depends(get_current_user)):
    if is_directory(path):
        return HTMLResponse(content=list_directory(path))
    else:
        return FileResponse(path=translate_path(path))
    
@app.post("/Files")
async def upload_file(path=None, file: UploadFile = File(...), user: str = Depends(get_current_user)):
    try:
        # 保存文件到服务器上的某个位置
        save_file = translate_path(path + "/" + file.filename if path else file.filename)
        with open(save_file, "wb") as buffer:
            buffer.write(await file.read())
        return HTMLResponse(content=list_directory(path))
    except Exception as e:
        return JSONResponse(content={"message": str(e)}, status_code=400)

def translate_path(path: str):
    if path:
        words = path.split('/')
        words = filter(None, words)
        path = config.FILES_BASE_PATH
        for word in words:
            if os.path.dirname(word) or word in (os.curdir, os.pardir):
                continue
            path = os.path.join(path, word)
        print(path)
        return path
    return config.FILES_BASE_PATH

def is_directory(path):
    return os.path.isdir(
        translate_path(path)
    )

def open_file(path):
    full_path = translate_path(path)
    print(full_path)
    with open(full_path) as rf:
        return rf.read()

def list_directory(path):
    full_path = translate_path(path)
    paths: list = []
    try:
        paths = os.listdir(full_path)
    except OSError:
        return None
    paths.sort(key=lambda a: a.lower())
    r = []
    enc = sys.getfilesystemencoding()
    title = 'Directory [/{}]'.format(path if path else "")
    r.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
                '"http://www.w3.org/TR/html4/strict.dtd">')
    r.append('<html>\n<head>')
    r.append('<meta http-equiv="Content-Type" '
                'content="text/html; charset=%s">' % enc)
    r.append('<title>%s</title>\n</head>' % title)
    r.append('<body>\n<h1>%s</h1>' % title)
    if path:
        r.append(
            "<form action=\"Files?path={}\" ENCTYPE=\"multipart/form-data\" method=\"post\">".format(
                path
            )
        )
    else:
        r.append(
            "<form action=\"Files\" ENCTYPE=\"multipart/form-data\" method=\"post\">"
        )
    r.append("<input ref=\"input\" multiple name=\"file\" type=\"file\"/>")
    r.append("<input type=\"submit\" value=\"上传文件\"/></form>\n")
    r.append('<hr>\n<ul>')
    for name in paths:
        fullname = path + "/" + name if path else name
        linkname = fullname
        displayname = name
        if is_directory(fullname):
            displayname = displayname + "/"
            linkname = linkname + "/"
        r.append('<li><a href="Files?path={}">{}</a></li>'.format(linkname, displayname))
    r.append('</ul>\n<hr>\n</body>\n</html>\n')
    encoded = '\n'.join(r)
    return encoded
