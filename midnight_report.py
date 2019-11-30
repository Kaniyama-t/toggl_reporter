import base64
import json
import urllib.request
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt

"""
TODOリスト
- toggl認証
- toggl_resを整形
- グラフ作成
- 前々日のデータ取得
"""

def main(event, context):
    ##########################################################################
    ## CONST
    #  - timezone
    jp_tz = datetime.timezone(datetime.timedelta(hours=9)) # 日本と指定
    #  - toggl token
    toggl_baseurl	=	"https://toggl.com/reports/api/v2/summary"
    #toggl_user		=	os.environ['toggl_user_id']
    toggl_wsid		=	os.environ['toggl_workspace_id']
    #toggl_token		=	os.environ['toggl_token']
    #  - slack
    slack_hook_url	=	os.environ['slack_incwebhook_url']
    #slack_token		=	os.environ['slack_token']

    ##########################################################################
    ## Getting toggl report
    #  - Create Date param
    """
    d = datetime.datetime.now(tz=jp_tz) - datetime.timedelta(days=1)
    toggl_since = d.isoformat()
    #  - Create Request
    toggl_headers={
        'Content-Type': 'application/json'
    }
    toggl_req_params = {
        'user_agent'    : 'webmaster@kaniyama.net',
        'workspace_id'  : toggl_wsid,
        'since'         : toggl_since
    }
    toggl_req = urllib.request.Request(generateGetUrl(toggl_baseurl,toggl_req_params), headers=toggl_headers)
    
	#  - Access to API.
    toggl_res = urllib.request.urlopen(toggl_req)
    toggl_res_body = json.load(toggl_res.read())

    print(toggl_res_body)#ForDEBUG
    """
    ##########################################################################
    ## Convert to ReportStack and Graph
    toggl_res_body = {}
    graphurl, stacks = togglResToReportStacks(toggl_res_body)
    
    # !!!!!ここDemoデータ ForDEBUG
    graphurl = "https://gyazo.com/b8b95342853b35152ded9341ee704fd7.png"
    stacks.append(
        ReportStack(
            title="学校勉強",
            time="1h0min.",
            converttime="1h0min.",
            client="School",
            stacktitle="Done List",
            stacklist=["微積（0h30min.）", "解析（0h30min.）"],
            stackicon="ballot_box_with_check"
        )
    )


    ##########################################################################
    ## Generate Slack's rich text and request.
    #  - Create Request
    slack_headers={
        'Content-Type'  :   'application/json',
    }
    slack_req_params = generateSlackPayload(stacks,graphurl)
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
    for p in params:
        url = url + p.key()+"="+p.value()+"&"

    return url[0:len(url)-1]

def togglResToReportStacks(res):
    #for p in toggl_res_body['data']:
    return None, []

def generateSlackPayload(reportstacks,graphurl):
    #  - Create Base Data.
    r = {
	"blocks": [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "*今日もお疲れ様です！* 詳しいレポートは<https://www.toggl.com/app/dashboard/me/3809938|こちらです！>"
			}
		}
    ]
    }

    # グラフを挿入
    graphsec = {"type":"image","alt_text": "graph"}
    graphsec['image_url'] = graphurl
    r['blocks'].append(graphsec)

    # 各プロジェクトごとにレイアウトを作成し挿入
    for stack in reportstacks:
        # 境界線挿入
        r['blocks'].append({"type": "divider"})
        # 中身挿入
        bodysec = 	{
        		"type": "section",
			    "text": {
			        "type": "mrkdwn"
		        },
                "fields":[],
	        	"accessory": {
		    		"type": "button",
		        	"text": {
			        	"type": "plain_text",
					    "text": "Share"
    			    }
			    }
            }
        ## プロジェクト名タイトル
        bodysec['text']['text']=":memo: *"+stack.Title+"*"
        
        ## 進捗時間
        timesec = {"type": "mrkdwn"}
        timesec['text'] = "*進捗*\n:stopwatch:"+stack.Time
        bodysec['fields'].append(timesec)
        
        ## 前日比時間
        convertsec = {"type": "mrkdwn"}
        ### TODO ここで比較し、上下平行でアイコン設定
        convertsec['text'] = "*前日比*\n :arrow_up_small: "+stack.ConvertTime
        #convertsec['text'] = "*前日比*\n :arrow_forward: 3h23min."
        #convertsec['text'] = "*前日比*\n :arrow_down: 3h23min."
        bodysec['fields'].append(convertsec)
        
        ## 進捗リスト
        stacksec = {"type": "mrkdwn"}
        stacksec['text'] = "*"+stack.StackTitle+"*"
        for p in stack.Stack:
            stacksec['text'] = stacksec['text'] + "\n:" + stack.StackIcon + ":" + p
        bodysec['fields'].append(stacksec)
        
        ## Shareボタンに送信する値情報
        bodysec['accessory']['value']=stack.Title

        
        # resultに挿入
        r['blocks'].append(bodysec)
    
    return r

class ReportStack:
    def __init__(self,title,time,converttime,client,stacktitle,stacklist,stackicon):
        self.Title=title
        self.Time=time
        self.ConvertTime=converttime
        self.Client=client
        self.StackTitle=stacktitle
        self.Stack=stacklist
        self.StackIcon=stackicon


if __name__ == "__main__":
    main(None,None)