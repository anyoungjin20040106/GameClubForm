from fastapi import FastAPI,Form,Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse,HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
import re
import os
import httpx
import html

pattern='^2(3|4)5(5|7)\d{3}$'
sheet=os.getenv('KGCmember')
programe=os.getenv('KGCPrograme')
templates = Jinja2Templates(directory="template")

app=FastAPI()
app.mount("/js", StaticFiles(directory="js"))
@app.get("/")
def index():
    return FileResponse('index.html')
@app.get("/insertform")
def insertform():
    return FileResponse('insert.html')
@app.post("/insert")
async def insert(request: Request,stnum:str=Form(...),name:str=Form(...),grade:int=Form(...),ph:str=Form(...),notes:str=Form(None)):
    form = {'mode': 'insert', 'stnum': stnum, "name": name, "grade": grade, "ph": ph, "notes": notes}
    if not re.match(pattern,stnum):
        return templates.TemplateResponse('warning.html',{'request':request,'msg':'빅데이터과나 영상미디어콘텐츠과만 가입이 가능합니다'})
    df=pd.read_excel(sheet)
    df=df[(df['학번']==stnum)|(df['연락처']==ph)]
    if len(df)>0:
        return templates.TemplateResponse('warning.html',{'request':request,'msg':'이미 가입되었습니다'})
    try:   
        async with httpx.AsyncClient() as client:
            response = await client.post(programe, data=form, follow_redirects=True)
            response.raise_for_status()
            msg = response.text
            msg = html.unescape(msg)
    except httpx.RequestError as e:
        msg = f'Google Sheets에 데이터 추가 중 오류 발생: {e}'
    except httpx.HTTPStatusError as e:
        msg = f'HTTP 오류 발생: {e.response.status_code} {html.unescape(e.response.text)}'
    return templates.TemplateResponse('success.html', {'request': request, 'msg': msg})
@app.get("/deleteform")
def delete():
    return FileResponse('delete.html')
@app.post("/delete")
async def delete(request: Request,stnum:str=Form(...),ph:str=Form(...)):
    df=pd.read_excel(sheet)
    df=df[(df['학번']==int(stnum))&(df['연락처']==ph)]
    if len(df)==0:
        return templates.TemplateResponse('warning.html',{'request':request,'msg':'학번과 전화번호를 확인해주세요'})
    form = {'mode': 'delete', 'stnum': stnum}
    try:   
        async with httpx.AsyncClient() as client:
            response = await client.post(programe, data=form, follow_redirects=True)
            response.raise_for_status()
            msg = response.text
            msg = html.unescape(msg)
    except httpx.RequestError as e:
        msg = f'Google Sheets에 데이터 추가 중 오류 발생: {e}'
    except httpx.HTTPStatusError as e:
        msg = f'HTTP 오류 발생: {e.response.status_code} {html.unescape(e.response.text)}'
    return templates.TemplateResponse('success.html', {'request': request, 'msg': msg})
@app.get("/updateform")
def update():
    return FileResponse('update.html')
@app.post("/updateinput")
async def updateinput(request: Request,stnum:str=Form(...)):
    stnum=int(stnum)
    df=pd.read_excel(sheet)
    df=df[df['학번']==stnum]
    if len(df)<1:
        return templates.TemplateResponse('warning.html',{'request':request,'msg':'해당 학번이 존재하지 않습니다'})
    df.set_index('학번',inplace=True)
    return templates.TemplateResponse('updateform.html',{'request':request,'stnum':stnum,'grade':df['학년'][stnum],'ph':df['연락처'][stnum],'name':df['성명'][stnum],'notes':df['비고'][stnum] })
@app.post("/update")
async def update(request: Request,stnum:str=Form(...),name:str=Form(...),grade:int=Form(...),ph:str=Form(...),notes:str=Form(None)):
    form = {'mode': 'update', 'stnum': stnum, "name": name, "grade": grade, "ph": ph, "notes": notes}
    try:   
        async with httpx.AsyncClient() as client:
            response = await client.post(programe, data=form, follow_redirects=True)
            response.raise_for_status()
            msg = response.text
            msg = html.unescape(msg)
    except httpx.RequestError as e:
        msg = f'Google Sheets에 데이터 추가 중 오류 발생: {e}'
    except httpx.HTTPStatusError as e:
        msg = f'HTTP 오류 발생: {e.response.status_code} {html.unescape(e.response.text)}'
    return templates.TemplateResponse('success.html',{'request':request,'msg':msg})
@app.get("/admincheck")
def admincheck():
    return FileResponse('admincheck.html')
@app.post("/admin")
def admin(request: Request,pw:str=Form(...)):
    df=pd.read_excel(sheet)
    dept={
    55:'빅데이터과',
    57:'영상미디어콘텐츠과'
    }
    df['학과']=df['학번'].apply(lambda x:dept[int(x%100000/1000)])
    df=df[['학과']+'학번	학년	성명	연락처	비고'.split()]
    df.reset_index(inplace=True)
    df.rename(columns={'index':'연번'},inplace=True)
    df['연번']=df['연번'].apply(lambda x:x+1)
    return templates.TemplateResponse('member.html',{'request':request,'table':df.to_html(index=False).replace("th","td").replace('class="dataframe"',"align='center'").replace('NaN',"")}) if pw==os.getenv("pw") else templates.TemplateResponse('warning.html',{'request':request,'msg':'암호를 틀렸습니다'})