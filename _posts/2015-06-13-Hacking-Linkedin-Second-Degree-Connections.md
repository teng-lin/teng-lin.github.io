---
title: BD Newbie: Hacking Linkedin Second Degree Connections
layout: post
---

When I was hunting for a new job I would repeatedly think to myself "I need to find a way to get introduced to more people". LinkedIn's API doesn't allow you to list the 2nd degree connections of your network, but through a few hacks we can get around this to get lists of people we can be introduced to.

To have a better understanding of unfamiliar market as a BD Newbie, you may want to talk to experts in your professional network. If you just blindly ask your friends whom in their network you should reach out to, the result is usually not very fruitful, unless you have a short list. [Linkedin](http://www.linkedin.com) certainly does not make it any easier, by limiting 10 connections to be shown at a time. LinkedIn does not provide an API to allow you to list the 2nd degree connections of your network. Fortunately, 

## Retrieve 2nd Degree Connections for a Given User

While LinkedIn's Official API does not allow you to retrieve 2nd degree connections for other users, [Ian Alexander](https://github.com/ianalexander/ianalexander/blob/master/content/blog/hacker-networking-hacking-the-linkedin-api.html) comes across a method to use Chrome's Developer Tools to uncover the "unoffical" browser/web API.



If you enable [Developer Tools](https://developer.chrome.com/devtools) Network tab, browse to your friend profile, and click on the connections, you will see a lot of requests being fired as the page is loaded. If you scroll to the bottom near your "Connections" section and click the "Next" button, you will see an interesting request fired:

{% syntax bash %}
https://www.linkedin.com/profile/profile-v2-connections?id={linkedin id}&offset=10&count=10&distance=0&type=INITIAL&_=1380053112371
{% endsyntax %}

`/profile-v2-connections` returns JSON data for your connections. It accepts both `offset` and `count` arguments. Note that,
change `count` to a number bigger than 10 will not have any effect, it will always return no more than 10 connections at a time. In other words, you have to change `offset` and repeat many times to retrieve all of the connections.

You can verfify if it works or not by right click on `/profile-v2-connections`, and click on "Open Link in New Tab" should return a `JSON` data in the new tab. 

A dirty python [script](/scripts/scrap_linkedin.py) is written to make this process a bit easier. To use the script,
you need to make sure you have `curl` binary, as well as `pandas` and `openpxyl` packages installed.

{% syntax bash%}
pip install pandas openpxyl
{% endsyntax %}

Right click on `/profile-v2-connections`, click on "Copy as cURL", open up a terminal and paste it after typeing `python scrap_linkedin.py`, and hit enter. Below is an example of the actual command line.

{% syntax bash %}
python scrap_linkedin.py curl 'https://www.linkedin.com/profile/profile-v2-connections?id=54617196&offset=0&count=10&distance=1&type=INITIAL&_=1434208146724' -H 'Cookie: bcookie="v=2&6789ccca-a705-4829-8306-6555c44011e5"; visit="v=1&M"; __qca=P0-341338068-1407868716823; VID=V_2014_10_31_02_1849; oz_props_fetch_size_14271099=15; bscookie="v=1&2015041013450300a40cce-bbbd-439e-8e62-b4b14a70da66AQGJAsMCqxO6TBwFHYFLdgOdHFRRhSuH"; L1l=1cff04a0; L1e=1ba80ac9; sessionid="eyJkamFuZ29fdGltZXpvbmUiOiJBbWVyaWNhL05ld19Zb3JrIn0:1Z09p1:3awkgMalmVHp0vD2Ov3VNv2nJy8"; _ga=GA1.2.1733979208.1432610629; L1c=14967427; lihc_auth_en=1434023164; lihc_auth_str=CkDwaEB41EB1IwId57eR7S%2Fyg1N%2BSvUL%2FXz%2F8eHDRMQSGixg4OGGXnGTnsRV0cxxNjw4V%2B7C5i6SlbGJ3N%2FqqZpiOUz2zgOQkK%2FaAtEqVcts1W84fQxUhJRsRdgpajl3whP8S9FsQT04ESoF0BNx23MTY686o4uPRr9BXH6s5b5sN7AqAt%2FaW%2BrKX%2BbfvBowVBNNpgJ%2Ffql2yFu31SKZObLVisKDtIveNDMkNTAyThixjBzxq00VxKwRWUnd8anuWl21GKVRm8Omo7m0OPvQa4Au7DZg6FMHaubc5RLApkuxMhCrku0f8OBvRN8tt0%2FLKa2B5dw2PYBClvdjii0ZoU3LE6G8dqlKrUXKLCScfEDq90GuBzqdog%3D%3D; sdsc=1%3A1SZM1shxDNbLt36wZwCgPgvN58iw%3D; share_setting=PUBLIC; csrftoken=ELrFZckA0IYhcWhc0DTkuYrECNUuL7Df; __utma=23068709.1733979208.1432610629.1434109323.1434170887.4; __utmc=23068709; __utmz=23068709.1433976462.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __utmv=23068709.user; _leo_profile=""; li_at=AQECAQDZwnsDeRYwAAABTezDPOYAAAFN7bgC2066yhW6CIYN_lrgaEPTdhEuT9drA_m8BrhexExP9uIdrUAJsPIDdcLvr-1Fsb3ADSzRexUkS0G3CvfXnZpQ6Y7rYegXAkPhSEIMfN16LQOTnBur2VQ; sl="v=1&DQ3z8"; JSESSIONID="ajax:2060657418974993997"; PLAY_SESSION="cc5f3a897af2a30f7700af681d01efda5731a309-chsInfo=5b877214-7cf7-498a-8bd2-eb0b7d5dcb65+nav_account_sub_nav_upgrade"; RT=s=1434208146416&r=https%3A%2F%2Fwww.linkedin.com%2Fprofile%2Fview%3Fid%3D13481474%26authType%3Dname%26authToken%3DcaBb%26trk%3Dprof-sb-browse_map-name; _lipt=0_2uw3Ir0voPvaeizPAkZsFLC1-YbKbTOElA77Zp4WwRU4408WI4yw6hJDL7tsw3tHVIovzh3Kjnmz-0JlOsHVOtZMikcnVqisVQkgceLH3JAyWlA9o4ULhFK2MvXoHwsD-94PGr7KuocxaMS6ZE5NCx1mtoPgrer8PUiCHUJ5YNeGfC4YUVC74Rcef-L7jlQb1XSpRJzvaynFK8VLWa8c1znJYxDlW5b0B6v-pqLfL6GxvpopYawNdh3mJsVoI5YmArCu5ynoM3q9nbyDGh52YBCR30bRvTYwU3IHBysHMe-maa0rMQsxDGRbkG8wspKNxa2XKJzE_inyHY0nv2m-Mk7HDhJnYJSBGdA0zzemYsn; lidc="b=TB99:g=75:u=34:i=1434208150:t=1434243098:s=AQEF_wVCK9WSoXYoXvkbWbzdd6z7byPZ"; lang="v=2&lang=en-us&c="' -H 'DNT: 1' -H 'Accept-Encoding: gzip, deflate, sdch' -H 'Accept-Language: en-US,en;q=0.8' -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36' -H 'Accept: text/plain, */*; q=0.01' -H 'Referer: https://www.linkedin.com/profile/view?id=54617196&authType=name&authToken=XsEh&trk=prof-sb-how_conn-name-link' -H 'X-Requested-With: XMLHttpRequest' -H 'Connection: keep-alive' --compressed
{% endsyntax %}

You can change the vaule of `id` to any given user and fire it away. An excel spreadsheet will be generated at the working directory.

