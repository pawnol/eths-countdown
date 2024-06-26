import os

from flask import Flask, render_template, current_app
from count.scrape_calendar import get_events
import json

def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        EAST_TROY_CALENDAR_URL='https://www.easttroy.k12.wi.us/pro/events_ical_subscribe.cfm?detailid=659489&categoryids=19&categoryids2=all&facultyflag=0'
    )

    @app.route('/')
    def index_page():
        return render_template('index.jinja')
    
    @app.route('/datesjson', methods=['GET'])
    def get_dates_json():
        # Load summary information
        original_summaries = []
        corrected_summaries = []
        default_summary = ""
        with current_app.open_resource('summaries.json') as f:
            f = json.load(f)
            for summary in f['summaries']:
                original_summaries.append(summary['given'])
                corrected_summaries.append(summary['corrected'])
            default_summary = f['default-summary']

        # Scrape event data
        events = get_events(current_app.config['EAST_TROY_CALENDAR_URL'], original_summaries)

        # Fix any dates that do not have a time
        for event in events['events']:
            if len(event['date']) < 25:
                with current_app.open_resource('time-corrections.json') as f:
                    f = json.load(f)
                    for t in f['times']:
                        if t['day-type'] in event['summary'].lower():
                            event['date'] = event['date'] + t['time']
                            break
                    else:
                        event['date'] = event['date'] + f['default-time']
        
        # Convert all summaries to corrected
        for event in events['events']:
            try:
                i = original_summaries.index(event['summary'])
                event['summary'] = corrected_summaries[i]
            except ValueError:
                event['summary'] = default_summary
        
        return events

    return app
