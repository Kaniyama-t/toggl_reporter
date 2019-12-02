import base64
import json
import urllib.request
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
import japanize_matplotlib
import math
import io
import requests


"""
TODOリスト
X toggl認証
X toggl_resを整形
X グラフ作成
X 前々日のデータ取得
- Github連携
X 文字化け対策
"""

def main(event, context):
    ##########################################################################
    ## CONST
    #  - timezone
    jp_tz = datetime.timezone(datetime.timedelta(hours=9)) # 日本と指定
    #  - toggl token
    toggl_baseurl	=	"https://toggl.com/reports/api/v2/summary"
    toggl_user		=	os.environ['toggl_user_id']
    toggl_wsid		=	os.environ['toggl_workspace_id']
    toggl_token		=	os.environ['toggl_token']
    #  - slack
    slack_hook_url	=	os.environ['slack_incwebhook_url']
    #slack_token		=	os.environ['slack_token']

    ##########################################################################
    ## Getting toggl report    
    #  - Create Authorication for Toggl report api v2
    toggl_headers={'Content-Type': 'application/json'}
    toggl_headers['Authorization'] = "Basic " + base64.b64encode('{}:{}'.format(toggl_token, 'api_token').encode('utf-8')).decode('utf-8')

    #  - Create Date param
    global toggl_today
    global toggl_yesterday
    global toggl_before_yesterday
    toggl_today = (datetime.datetime.now(tz=jp_tz) - datetime.timedelta(days=0)).strftime("%Y-%m-%d")
    toggl_yesterday = (datetime.datetime.now(tz=jp_tz) - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    toggl_before_yesterday = (datetime.datetime.now(tz=jp_tz) - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
    
    #  - Create parameters
    toggl_req_params = {}
    toggl_req_params['user_agent']=toggl_user
    toggl_req_params['workspace_id']=toggl_wsid
    toggl_req_params['since']=toggl_yesterday
    toggl_req_params['until']=toggl_yesterday
    print(generateGetUrl(toggl_baseurl,toggl_req_params))#FOrDEBUG

    ## - Today's Data
    #  - Connect to toggl report api v2 Summary Report
    toggl_req = urllib.request.Request(generateGetUrl(toggl_baseurl,toggl_req_params), headers=toggl_headers)
    toggl_res = urllib.request.urlopen(toggl_req).read()
    #  - Parse from urllib obj to json
    toggl_res_json = json.loads(toggl_res)

    print(toggl_res_json)#ForDEBUG
    print("")

    ## - Yesterday's Data
    toggl_req_params['since']=toggl_before_yesterday
    toggl_req_params['until']=toggl_before_yesterday
    toggl_req_y = urllib.request.Request(generateGetUrl(toggl_baseurl,toggl_req_params), headers=toggl_headers)
    toggl_res_y = urllib.request.urlopen(toggl_req_y).read()
    #  - Parse from urllib obj to json
    toggl_res_y_json = json.loads(toggl_res_y)

    print(toggl_res_y_json)#ForDEBUG

    ##########################################################################
    ## Convert to ReportStack and Graph
    totaltime, graphurl, stacks = togglResToReportStacks(toggl_res_json, toggl_res_y_json)
    
    ##########################################################################
    ## Generate Slack's rich text and request.
    #  - Create Request
    slack_headers={
        'Content-Type'  :   'application/json',
    }
    slack_req_params = generateSlackPayload(totaltime,stacks,graphurl)
    slack_req_params['channel'] = '#alert'
    slack_req_params['username'] = 'Toggl Report'
    slack_req_params['icon_url'] = 'https://i0.wp.com/www.ttcbn.net/wp/wp-content/uploads/2013/07/Toggl1.jpg?fit=512%2C512&ssl=1'
    
    slack_req = urllib.request.Request(slack_hook_url, json.dumps(slack_req_params).encode(), slack_headers)
    with urllib.request.urlopen(slack_req) as slack_res:
        print(slack_res.read())

    
    # =========================== END ==================================
    
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
#    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
#    print(pubsub_message)

def generateGetUrl(url,params):
    url = url + "?"
    for pk,pv in params.items():
        url = url + pk + "=" + pv + '&'

    return url[0:len(url)-1]

def togglResToReportStacks(res, res_y):
    gyazo_token		=	os.environ['gyazo_token']
    # ReportStacks
    totaltime=0
    resp=[]
    
    # Graph
    graph_p=[]
    graph_l=[]
    graph_c=[]

    # Analyzing all time topics.
    for p in res['data']:
        # calcurate total time
        totaltime = totaltime + p['time']

        # title
        if p['title']['project'] == None:
            p['title']['project'] = "休憩"

        # title icon
        titleicon = "::"
        if p['title']['project'] == "勉強" or p['title']['project'] == "試験":
            titleicon=":memo:"
        elif p['title']['hex_color'] == "#3750b5":
            titleicon=":computer:"
        elif p['title']['project'] == "休憩":
            titleicon=":coffee:"
        else:
            titleicon=":grey_question:"

        # convert time
        ctime=None
        for i, y in enumerate(res_y['data']):
            if y['title']['project'] == None:
                y['title']['project'] = "休憩"
            print(str(p['title']['project'])+"("+ str(p['time']) + ") ?= " + str(y['title']['project']) +"("+ str(y['time']) + ")[" + str(i) + "], ctime=" + str(ctime))
            if p['title']['project'] == y['title']['project']:
                # 計算
                ctime = p['time'] - y['time']
                print("DECIDED :: "+str(p['title']['project']) + " ?= " + str(y['title']['project'])  +"[" + str(i) + "], ctime=" + str(ctime))
                del res_y['data'][i]
                break

        # color
        if p['title']['hex_color'] == None:
            p['title']['hex_color'] = "#DDDDDD"
        
        # stack title and list (depends on client)
        stack=[]
        for pp in p['items']:
            stack.append((":ballot_box_with_check:",pp['title']['time_entry'])) 
        #if p['title']['client'] == "https://github^^^^":
        
        # if NotNotify tag is NOT Set,
        if p['title']['client'] != "NotNotify":
            # [append] Graph params
            graph_p.append(p['time'])
            graph_l.append(p['title']['project'])
            graph_c.append(p['title']['hex_color'])

            # [append] to resp for slack rich text
            resp.append(
                ReportStack(
                    title=p['title']['project'],
                    titleIcon=titleicon,
                    color=p['title']['hex_color'],
                    time=msecToHours(p['time']),
                    converttime=ctime,
                    client=p['title']['client'],
                    stacktitle="やったこと",
                    stacklist=stack
                )
            )
    
    # Create Graph
    plt.pie(graph_p, labels=graph_l, colors=graph_c, counterclock=False, startangle=90,wedgeprops={'linewidth': 3, 'edgecolor':"white"})
    # 中心 (0,0) に 60% の大きさで円を描画
    centre_circle = plt.Circle((0,0),0.9,color='black', fc='white',linewidth=1.25)
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    # io を用いてメモリ上に保存
    format = "png"
    sio = io.BytesIO()
    plt.savefig(sio, format=format)
    # グラフの出力をしない
    plt.close(fig)

    # GyazoへUpload
    # gyazo_headers={
    #     'Content-Type'  :   'multipart/form-data',
    # }
    # gyazo_headers['Authorization'] = "Bearer " + gyazo_token
    gyazo_params={
        'access_token': gyazo_token
    }
    gyazo_file = {
        'imagedata': sio.getvalue()
    }
    gyazo_res = requests.post(
        url     = "https://upload.gyazo.com/api/upload",
        params  = gyazo_params,
        files   = gyazo_file )
    gyazo_res_json = gyazo_res.json()
    gyazo_img_url = gyazo_res_json['url']
    
    gyazo_res.close()

    return totaltime, gyazo_img_url, resp

def msecToHours(time):
    return str(math.floor(time/(1000*60*60)))+"h "+str(math.floor(time/(1000*60))%60)+"min."

def generateSlackPayload(totaltime,reportstacks,graphurl):
    #  - Create Base Data.
    r = {
        "text": "*今日もお疲れ様です！*\n詳しいレポートは<https://www.toggl.com/app/dashboard/me/3809938|こちらです！>",
        "attachments": []
    }

    # グラフを挿入
    graphsec = {"fields": []}
    graphsec['text']= "*" + toggl_yesterday + "'s report*\n*Total time：" + msecToHours(totaltime) + "*"
    graphsec['image_url'] = graphurl
    graphsec['mrkdwn_in'] = ['text']
    r['attachments'].append(graphsec)

    # 各プロジェクトごとにレイアウトを作成し挿入
    for stack in reportstacks:
        # 中身挿入
        bodysec = {'fields':[]}
        ## プロジェクト名タイトル
        bodysec['title'] = stack.TitleIcon + stack.Title
        bodysec['color'] = stack.Color
        
        ## 進捗時間
        timesec={}
        timesec['title'] = "進捗"
        timesec['value'] = ":stopwatch:"+stack.Time
        timesec['short'] = True
        bodysec['fields'].append(timesec)
        
        ## 前日比時間
        convertsec = {}
        convertsec['title'] = "前日比"
        convertsec['short'] = True
        if stack.Title == "休憩":
            if stack.ConvertTime == None:
                convertsec['value'] = ":new:  -  "
            elif stack.ConvertTime > 0:
                convertsec['value'] = ":arrow_up: "+msecToHours(stack.ConvertTime)
            elif stack.ConvertTime == 0:
                convertsec['value'] = ":arrow_forward: "+msecToHours(stack.ConvertTime)
            else:
                convertsec['value'] = ":arrow_down_small: "+msecToHours(stack.ConvertTime)
        else:
            if stack.ConvertTime == None:
                convertsec['value'] = ":new:  -  "
            elif stack.ConvertTime > 0:
                convertsec['value'] = ":arrow_up_small: "+msecToHours(stack.ConvertTime)
            elif stack.ConvertTime == 0:
                convertsec['value'] = ":arrow_forward: "+msecToHours(stack.ConvertTime)
            else:
                convertsec['value'] = ":arrow_down: "+msecToHours(stack.ConvertTime)
        bodysec['fields'].append(convertsec)
        
        ## 進捗リスト
        stacksec = {}
        stacksec['title'] = stack.StackTitle
        stacksec['value'] = ""
        stacksec['short'] = False
        initFlag = True
        for p in stack.Stack:
            if initFlag == True:
                initFlag = False
            else:
                stacksec['value'] = stacksec['value'] + "\n"
            
            stacksec['value'] = stacksec['value'] + p[0] + " " + p[1]
        
        bodysec['fields'].append(stacksec)
        
        # resultに挿入
        r['attachments'].append(bodysec)
    
    return r

class ReportStack:
    def __init__(self,title,titleIcon,color,time,converttime,client,stacktitle,stacklist):
        self.Title=title
        self.TitleIcon=titleIcon
        self.Color=color
        self.Time=time
        self.ConvertTime=converttime
        self.Client=client
        self.StackTitle=stacktitle
        self.Stack=stacklist


if __name__ == "__main__":
    main(None,None)