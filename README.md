# streamchicken

Backend components for the new timvideos.us streaming website.

## Setup

```
pip install -r requirements.txt
```

### crontab

```
*/5 * 14-31 1 * /home/website2/tools/update_twitter.sh
2 * 14-31 1 * /home/website2/tools/update_schedule.sh
```

### nginx

We run nginx behind Cloudflare (which provides HTTPS).  We need it to cache some of our content for shorter times than the rest, and we don't care about sharing that JSON cache between multiple clients.  This should clamp hits to distinct resources in `/dynamic/` at around 1 per 5 minutes.

TODO: Add proper cache values for the rest of the website as well.

```
server {
	listen 80;
	server_name timvideos.us;

	# path for static files
	root /home/website2/html;

	location /dynamic/ {
		# We should expire all these things within 5 min
		expires 5m;
		add_header Pragma public;
		add_header Cache-Control "public";
	}
}
```

## Design

This has two halves:

* A frontend component written using React, which contains the UI of the application (written by @joeladdison)

* A backend component written using Python, which generates all the data consumed by the React UI. (this repository)

The entire website can be hosted using a static web server.  This could also probably moved to some cloud file storage system, provided that it is possible to expire the objects within reasonable timeframes.

## Configuration

### Scheduling

See `update_schedule.sh`.  This will grab a schedule from veyepar, and the `rooms.json`, and generate a `schedule.json` from the two parts.

`rooms.json` is a JSON object with:

- `tz`: string containing an Olsen timezone name to localise all timestamps to. It assumes that veyepar will give bare ISO 8601 timestamps in local time, and fixes them up.

- `rooms`: array of Room objects:

  - `id`: The `location_slug` from veyepar for the room. This is used to determine subpages in the frontend component.
  
  - `name`: A human-friendly name for the room.  This can't be too long, so consider truncating to around 16 characters.
  
  - `youtube`: A YouTube video ID for the live stream in the room.  eg: https://www.youtube.com/watch?v=dQw4w9WgXcQ becomes `dQw4w9WgXcQ`

When setting up the room each day, you'll need to edit `rooms.json`, put in the day's YouTube stream ID, and then run `update_schedule.sh`.  That'll push the update out to the website.

### Twitter feed

See `update_twitter.sh`.  This will take in two Twitter configuration files, `twitter_config.ini` and `twitter_secrets.ini`.

#### `twitter_config.ini`

This contains the non-private configuration for the Twitter scraper.

- `[twitter]`: The only section of the file

  - `announcements`: This is the Twitter account used for announcements. This must be a single user, and start with `@`.
  
  - `search`: A search query to be used for the main feed. You can also add `AND -filter:retweets AND -filter:replies` to show more diverse content (rather than many people retweeting the same thing).
    
    An example would be `#lca2018 AND -filter:retweets AND -filter:replies`.
  
  - `geo`: A comma-separated list of `lat,long,radius` of where to geo-restrict searches to.  This works on both geotagged and non-geotagged tweets, by Twitter doing a geo-IP lookup on the sender.  Radius needs to be specified with a unit in kilometres (eg: `20km`).
    
    This is useful for taking unrelated/spammy non-local use of the same hashtag out of the stream, and is _required_.
  
  - `count`: The number of recent tweets to display.
  
  - `tz`: An Olsen timezone name to localise all timestamps to. It assumes that Twitter will give bare ISO 8601 timestamps in UTC, and fixes them up.

#### `twitter_secrets.ini`

This contains private information for the Twitter scraper.

- `[api]`: The only section of the file.

  - `consumer_key`: A Twitter consumer key for the application.
  
  - `consumer_secret`: A Twitter consumer secret for the application.
  
  - `access_token`: A Twitter access token for the user.
  
  - `access_token_secret`: A Twitter access token secret for the user.
