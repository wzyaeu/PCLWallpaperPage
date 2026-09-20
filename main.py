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
    
    return [date_str]+result
    
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
    load_template('mainpage/visablebox')
    load_template('mainpage/visablebox_foot')

    all_date_data = []
    count = 12
    output = ''
    print('mainpage-构建页面')
    print(f'mainpage-获取api数据')
    alldate_data = requests.get(f'https://uapis.cn/api/v1/image/bing-daily/history?page_size={count}').json()['items']
    start_day = get_previous_days(alldate_data[0]['date'], count)
    print(start_day)
    for index in range(0, count):
        date_data = alldate_data[index]
        print(f'mainpage-构建页面-{index}/{count} {date_data['date']}')
        output += replaces(templates['mainpage/imagebox'],{
            'visable': ''.join([replaces(templates['mainpage/visablebox'],{
                'date': d
            }) for d in start_day if d != date_data['date']]),
            'visable-foot': ''.join([templates['mainpage/visablebox_foot']]*(count-1)),
            'page_default':'Visible' if index == 1 else 'Collapsed',
            'img':escape_xaml(date_data['image_url_1080']),
            'img_4k':escape_xaml(date_data['image_url_4k']),
            'title':escape_xaml(date_data['title']),
            'date':escape_xaml(date_data['date']),
            'sub-title':escape_xaml(date_data.get('headline', date_data.get('subtitle', date_data['title']))),
            'desc':escape_xaml(date_data.get('description', '')),
            'download_name':escape_xaml(date_data['date']+'-1080P的图片.jpg'),
            'download_name_4k':escape_xaml(date_data['date']+'-4K的图片.jpg'),
            'left_btn':replaces(templates['mainpage/left_btn'],{
                'page': alldate_data[index]['date'],
                'last': alldate_data[index+1]['date'] if index != count-1 else '滚木',
                'hit': 'True' if index != count-1 else 'False',
                'opac': '1' if index != count-1 else '0.5',
            }),
            'right_btn':replaces(templates['mainpage/right_btn'],{
                'page': alldate_data[index]['date'],
                'last': alldate_data[index-1]['date'] if index != 0 else '滚木',
                'hit': 'True' if index != 0 else 'False',
                'opac': '1' if index != 0 else '0.5',
            }),
        })
    print('mainpage-保存输出文件')
    save_output_file('Custom.xaml',replaces(templates['mainpage'],{
        'images':output,
        'gv':BUILD_VERSION,
        'sponsors':'\n'.join([replaces(templates['sponsors'],{
            'sponsor': s
        }) for s in sponsors])
    }))
    save_output_file('Custom.xaml.ini',BUILD_VERSION)
    save_output_file('Custom.json',json.dumps(
        {
            "Title": "Wallpaper 每日壁纸"
        }
    ,ensure_ascii=False))

def redirects():
    with open(os.path.join(OUTPUT_PATH, '_redirects'), 'w', encoding='utf-8') as f:
        f.write('''/ /Custom.xaml 200
/version /Custom.xaml.ini 200''')

def init():
    print('init-初始化中')
    global OUTPUT_PATH, BASE_PATH, BUILD_VERSION, templates, ncm, test_environment, today, sponsors
    templates = {}
    BUILD_VERSION = secrets.token_hex(4)
    BASE_PATH = os.path.dirname(__file__)
    OUTPUT_PATH = os.path.join(BASE_PATH,'output')
    shutil.rmtree(OUTPUT_PATH,ignore_errors=True)
    os.makedirs(OUTPUT_PATH,exist_ok=True)
    today = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d')
    sponsors = requests.get('https://v4.gh-proxy.org/https://github.com/wzyaeu/IfadianSponsorGet/raw/refs/heads/pagedata/output.json').json()

    print('init-运行mainpage')
    mainpage()

    # print('init-运行historypage')
    # historypage()

    print('init-运行redirects')
    redirects()

init()