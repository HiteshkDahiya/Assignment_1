import datetime

# def get_date_info(date_str: str) -> dict:
#     """
#     date_str example: '26 dec 2025'
#     """
#     parsed_date = datetime.datetime.strptime(date_str, "%d %b %Y").date()

#     return {
#         "date": parsed_date.isoformat(),
#         "weekday": parsed_date.strftime("%A"),
#         "weekday_index": parsed_date.weekday(),   # 0=Mon ... 6=Sun
#         "is_working_day": parsed_date.weekday() < 5
#     }

#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def get_current_time() -> str:  
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %I:%M:%S %p")

print(get_current_time())


def get_time_after_hours(hours: int) -> str:
    now = datetime.datetime.now()
    future_time = now + datetime.timedelta(hours=hours)
    return future_time.strftime("%Y-%m-%d %I:%M:%S %p")

print(get_time_after_hours(2))