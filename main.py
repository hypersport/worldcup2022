import uuid
import requests
import datetime
from icalendar import Calendar, Event, Alarm


def get_data() -> list:
    urls = []
    data = []
    game_days = [
        '11-20', '11-21', '11-22', '11-23', '11-24', '11-25', '11-26', '11-27',
        '11-28', '11-29', '11-30', '12-01', '12-02', '12-03', '12-04', '12-05',
        '12-06', '12-08', '12-09', '12-10', '12-13', '12-14', '12-16', '12-17'
    ]
    base_url = 'https://tiyu.baidu.com/api/match/%E4%B8%96%E7%95%8C%E6%9D%AF/live/date/2022-{}/direction/after'

    for day in game_days:
        url = base_url.format(day)
        resp = requests.get(url)
        for info in resp.json()['data'][0]['list']:
            data.append(info)
    return data


def parse_data(data: dict) -> dict:
    d = {}
    name1 = data['leftLogo']['name']
    name2 = data['rightLogo']['name']
    score1 = '' if data['leftLogo']['score'] == '-' else data['leftLogo']['score']
    score2 = '' if data['rightLogo']['score'] == '-' else data['rightLogo']['score']
    d['summary'] = f'{name1} VS {name2} - {score1} : {score2}' if score1 and score2 else f'{name1} VS {name2}'
    d['summary'] += f'\n{data["matchName"]}'
    d['dtstart'] = datetime.datetime.strptime(
        data['startTime'], '%Y-%m-%d %H:%M:%S')
    d['dtend'] = d['dtstart'] + datetime.timedelta(hours=2)
    d['description'] = data['matchName']
    d['uid'] = str(uuid.uuid4())
    return d


def get_event(data: dict, is_alarm: bool = False, minutes: int = 30) -> Event:
    event = Event()
    for k, v in data.items():
        event.add(k, v)
    if is_alarm:
        alarm = Alarm()
        alarm.add('trigger', datetime.timedelta(minutes=-minutes))
        alarm.add('action', 'DISPLAY')
        alarm.add('description', f'比赛 {minutes} 分钟后开始')
        event.add_component(alarm)
        event.fromkeys
    return event


def get_events(match_data: list, with_alarms: bool = False) -> list:
    events = []
    for data in match_data:
        event_data = parse_data(data)
        if with_alarms:
            is_end = '-' in event_data['summary'] and ':' in event_data['summary']
            events.append(get_event(event_data, not is_end))
        else:
            events.append(get_event(event_data))
    return events


def get_calendar(events) -> Calendar:
    cal = Calendar()
    cal.add('prodid', '-//Hypersport//hypersport.club//')
    cal.add('version', '2.0')
    cal.add('method', 'PUBLISH')
    cal.add('X-WR-TIMEZONE', 'Asia/Shanghai')
    cal.add('x-wr-calname', '2022 卡塔尔世界杯')
    for event in events:
        cal.add_component(event)
    return cal


def save_calendar(cal: Calendar, filename: str) -> None:
    with open(filename, 'wb') as f:
        f.write(cal.to_ical())


if __name__ == '__main__':
    data = get_data()
    events_with_alarms = get_events(match_data=data, with_alarms=True)
    calendar_with_alarms = get_calendar(events=events_with_alarms)
    save_calendar(cal=calendar_with_alarms,
                  filename='./worldcup2022_alarms.ics')
    events_without_alarms = get_events(match_data=data)
    calendar_without_alarms = get_calendar(events=events_without_alarms)
    save_calendar(cal=calendar_without_alarms, filename='./worldcup2022.ics')

    # Save to markdown
    num = 1
    content = '''# 2022 卡塔尔世界杯赛程日历订阅

### 订阅地址:

> 1. [仅赛程无提醒](https://pythonista.cn/static/upload/worldcup2022.ics)

> 2. [赛前半小时提醒](https://pythonista.cn/static/upload/worldcup2022_alarms.ics)

### 订阅方法:

> iPhone/Mac/iPad Safari 浏览器直接打开上面链接, 默认打开日历, 点击完成即可订阅 ~~, 之后数据每天会自动更新~~.

### 比赛信息:
  |||||||||
  |:---:|:---|:---|:---:|---:|---:|:---:|:---:|
'''
    with open('./README.md', 'w') as f:
        for info in data:
            content += f"  |{num}|{info['leftLogo']['name']}|{info['leftLogo']['score']}| : |{info['rightLogo']['score']}|{info['rightLogo']['name']}|{info['matchName']}|{info['startTime'][:-3]}|\n"
            num += 1
        f.write(content)
