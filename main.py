import os
import secrets
import shutil
import requests
import json
from datetime import datetime, timezone, timedelta

def load_template(name, noxaml = False):
    print(f'load_template-加载模板文件-{name}')
    global templates
    if not name in templates:
        t_path = os.path.join(BASE_PATH, 'templates', name+('' if noxaml else '.xaml'))
        with open(t_path,'r', encoding='utf-8') as f:
            templates[name] =  f.read()

def save_output_file(name, data):
    print(f'save_output_file-保存输出文件-{name}')
    o_path = os.path.join(BASE_PATH, 'output', name)
    with open(o_path,'w', encoding='utf-8') as f:
        f.write(data)

def replaces(string: str, s: dict):
    output = string
    for l, d in s.items():
        output = output.replace('{'+l+'}', str(d))
    return output

def get_previous_days(date_str, x):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    
    result = []
    for i in range(1, x):
        prev_date = date_obj - timedelta(days=i)
        result.append(prev_date.strftime('%Y-%m-%d'))
    
    return [today]+result
    
def nlv(s):
    return '\\n'.join(str(s).splitlines())

def escape_xaml(text):
    if text is None:
        return ''
    return (
        text.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;')
             .replace('"', '&quot;')
             .replace("'", '&apos;')
    )

def mainpage():
    global all_date_data
    print('mainpage-开始')
    print('mainpage-加载模板')
    load_template('mainpage')
    load_template('mainpage/imagebox')
    load_template('mainpage/left_btn')
    load_template('mainpage/right_btn')
    load_template('mainpage/test_btn')

    all_date_data = []
    count = 10
    output = ''
    print('mainpage-构建页面')
    for index, date in enumerate(get_previous_days(today, count), start=1):
        print(f'mainpage-构建页面-{index}/{count}')
        print(f'mainpage-获取api数据-{date}')
        date_data = requests.get(f'https://uapis.cn/api/v1/image/bing-daily?format=json&resolution=1080&date={date}&mkt=zh-CN').json()
        output += replaces(templates['mainpage/imagebox'],{
            'page':index,
            'page_default':'Visible' if index == 1 else 'Collapsed',
            'img':escape_xaml(date_data['image_url']),
            'img_4k':escape_xaml(date_data['image_url_4k']),
            'title':escape_xaml(date_data['title']),
            'date':escape_xaml(date_data['date']),
            'sub-title':escape_xaml(date_data['headline']),
            'desc':escape_xaml(date_data['description']),
            'download_name':escape_xaml(date_data['date']+'的图片.jpg'),
            'left_btn':replaces(templates['mainpage/left_btn'],{
                'page': index,
                'last': index+1,
                'hit': 'True' if index != count else 'False',
                'opac': '1' if index != count else '0.5',
            }),
            'right_btn':replaces(templates['mainpage/right_btn'],{
                'page': index,
                'last': index-1,
                'hit': 'True' if index != 1 else 'False',
                'opac': '1' if index != 1 else '0.5',
            }),
            'test':escape_xaml(date_data['trivia']['question']),
            'test_btn':'\n'.join([
                replaces(templates['mainpage/test_btn'],{
                    'bullet': o['bullet'],
                    'text': escape_xaml(o['text']),
                    'url': escape_xaml(o['url']),
                })
                for o in date_data['trivia']['options']
            ]),
        })
        all_date_data.append({
            'date': date_data['date'],
            'title': date_data['headline'],
            'name': date_data['title'],
            'desc': date_data['description'],
            'image': {
                '4k': date_data['image_url_4k'],
                '1080p': date_data['image_url'],
            },
            'question': {
                'title':date_data['trivia']['question'],
                'options': [{
                    'text': o['text'],
                    'url': o['url'],
                } for o in date_data['trivia']['options']]
            },
        })
    print('mainpage-保存输出文件')
    save_output_file('Custom.xaml',replaces(templates['mainpage'],{
        'images':output,
        'gv':BUILD_VERSION
    }))
    save_output_file('Custom.xaml.ini',BUILD_VERSION)

def publicdata():
    print('publicdata-保存文件')
    public_path = os.path.join(OUTPUT_PATH, 'public')
    os.makedirs(public_path,exist_ok=True) 
    with open(os.path.join(public_path, 'wallpaper.json'), 'w', encoding='utf-8') as f:
        json.dump(all_date_data, f, ensure_ascii=False)

def redirects():
    with open(os.path.join(OUTPUT_PATH, '_redirects'), 'w', encoding='utf-8') as f:
        f.write('''/ /Custom.xaml 200
/version /Custom.xaml.ini 200''')

def init():
    print('init-初始化中')
    global OUTPUT_PATH, BASE_PATH, BUILD_VERSION, templates, ncm, test_environment, today
    templates = {}
    BUILD_VERSION = secrets.token_hex(4)
    BASE_PATH = os.path.dirname(__file__)
    OUTPUT_PATH = os.path.join(BASE_PATH,'output')
    shutil.rmtree(OUTPUT_PATH,ignore_errors=True)
    os.makedirs(OUTPUT_PATH,exist_ok=True)
    today = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d')

    print('init-运行mainpage')
    mainpage()

    print('init-运行publicdata')
    publicdata()

    # print('init-运行historypage')
    # historypage()

    print('init-运行redirects')
    redirects()

init()