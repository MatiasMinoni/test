from pytz import timezone
from typing import AnyStr
from datetime import datetime


class CTime:

    def __init__(self) -> None:
        self._time_zone = 'Europe/Madrid'

    @property
    def time_zone(self) -> AnyStr:
        return timezone(self._time_zone)

    @property
    def current_time(self) -> AnyStr:

        return self._current_time()

    @time_zone.setter
    def time_zone(self, value: AnyStr):
        self._time_zone = value

    def _current_time(self) -> AnyStr:

        current_date = datetime.now(self.time_zone).strftime('%H:%M')

        return current_date.split(':')[0]+':'+self._fix_minutes(current_date.split(':')[1])

    def _fix_minutes(self, minutes: AnyStr) -> AnyStr:

        return '0'+minutes if len(minutes) == 1 else minutes

if __name__ == '__main__':
    time = CTime()
    print(time.current_time)