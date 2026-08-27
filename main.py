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
    for i in range(1, x + 1):
        prev_date = date_obj - timedelta(days=i)
        result.append(prev_date.strftime('%Y-%m-%d'))
    
    return result
    
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
    print('mainpage-开始')
    print('mainpage-加载模板')
    load_template('mainpage')

    print('mainpage-构建页面')
    output = replaces(templates['mainpage'],{
        'img':escape_xaml(image_data['image_url']),
        'img_4k':escape_xaml(image_data['image_url_4k']),
        'title':escape_xaml(image_data['title']),
        'date':escape_xaml(image_data['date']),
        'sub-title':escape_xaml(image_data['headline']),
        'desc':escape_xaml(image_data['description']),
        'download_name':escape_xaml(image_data['date']+'的图片.jpg'),
        'gv':BUILD_VERSION
    })
    print('mainpage-保存输出文件')
    save_output_file('Custom.xaml',output)
    save_output_file('Custom.xaml.ini',BUILD_VERSION)

def historypage():
    print('historypage-开始')
    print('historypage-加载模板')
    load_template('historypage')
    load_template('history_image')

    count = 7
    output = ''
    for index, date in enumerate(get_previous_days(today, count), start=1):
        print(f'historypage-构建页面-{index}/{count}')
        print(f'historypage-获取api数据-{date}')
        date_data = requests.get(f'https://uapis.cn/api/v1/image/bing-daily?format=json&resolution=1080&date={date}').json()
        output += replaces(templates['history_image'],{
            'img':escape_xaml(date_data['image_url']),
            'img_4k':escape_xaml(date_data['image_url_4k']),
            'title':escape_xaml(date_data['title']),
            'date':escape_xaml(date_data['date']),
            'sub-title':escape_xaml(date_data['headline']),
            'desc':escape_xaml(date_data['description']),
            'download_name':escape_xaml(date_data['date']+'的图片.jpg'),
        })
    print('historypage-保存输出文件')
    output = replaces(templates['historypage'],{
        'image':output
    })
    save_output_file('history.xaml',output)
    save_output_file(f'history.json',json.dumps(
        {
            'Title': f'历史画廊'
        }
    ,ensure_ascii=False))

def init():
    print('init-初始化中')
    global OUTPUT_PATH, BASE_PATH, BUILD_VERSION, templates, ncm, test_environment, image_data, today
    templates = {}
    BUILD_VERSION = secrets.token_hex(4)
    BASE_PATH = os.path.dirname(__file__)
    OUTPUT_PATH = os.path.join(BASE_PATH,'output')
    shutil.rmtree(OUTPUT_PATH,ignore_errors=True)
    os.makedirs(OUTPUT_PATH,exist_ok=True)
    today = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d')

    print('init-获取api数据')
    image_data = requests.get(f'https://uapis.cn/api/v1/image/bing-daily?format=json&resolution=1080&date={today}').json()

    print('init-运行mainpage')
    mainpage()

    print('init-运行historypage')
    historypage()

init()