import uuid
import requests
import datetime
from icalendar import Calendar, Event, Alarm


def get_urls() -> list:
    urls = []
    game_days = [
        '11-20', '11-21', '11-22', '11-23', '11-24', '11-25', '11-26', '11-27',
        '11-28', '11-29', '11-30', '12-01', '12-02', '12-03', '12-04', '12-05',
        '12-06', '12-08', '12-09', '12-10', '12-13', '12-14', '12-16', '12-17'
    ]
    base_url = 'https://tiyu.baidu.com/api/match/%E4%B8%96%E7%95%8C%E6%9D%AF/live/date/2022-{}/direction/after'

    for day in game_days:
        urls.append(base_url.format(day))
    return urls


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
    return event


def get_events_without_alarm(urls: list) -> list:
    events = []
    for url in urls:
        resp = requests.get(url)
        for data in resp.json()['data'][0]['list']:
            event_data = parse_data(data)
            events.append(get_event(event_data))
    return events


def get_events_with_alarm(urls: list) -> list:
    events = []
    for url in urls:
        resp = requests.get(url)
        for data in resp.json()['data'][0]['list']:
            event_data = parse_data(data)
            is_end = '-' in event_data['summary'] and ':' in event_data['summary']
            events.append(get_event(event_data, not is_end))
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


def sava_calendar(cal: Calendar, filename: str) -> None:
    with open(filename, 'wb') as f:
        f.write(cal.to_ical())


if __name__ == '__main__':
    urls = get_urls()
    events_with_alarms = get_events_with_alarm(urls=urls)
    calendar_with_alarms = get_calendar(events=events_with_alarms)
    sava_calendar(cal=calendar_with_alarms,
                  filename='./worldcup2022_alarms.ics')
    events_without_alarms = get_events_without_alarm(urls=urls)
    calendar_without_alarms = get_calendar(events=events_without_alarms)
    sava_calendar(cal=calendar_without_alarms, filename='./worldcup2022.ics')
