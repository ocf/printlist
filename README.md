# Print List
Displays the print queue of Berkeley OCF printers on a web page for easy viewing.

> **Dependencies:** redis, flask, gunicorn

### Developer Environment

> Testing out Print List locally

The developer environment can be initiated through the command:

`python3 main.py --dev`

This will override redis functions within `main.py` with `redis_mimic.py` . This mimic of redis will send printing requests that act as a mock to the actual redis.

#### Redis Messages

> The format of redis messages over the channel of printer-*

```json
{
    "user": "username",
    "time": 0.0,
    "status": 0,
    "id": 0
}
```

Where status corresponds to the following:

**0** - Print job is completed

**1** - Print job is currently pending

**2** - Print job has been canceled due to a problematic file

**3** - Print job has been canceled due exceeding daily quota of printing

**4** - Print job has encountered an unexpected error

See first [implementation](https://github.com/ocf/puppet/pull/866) of status codes for more

#### How does Print List work?

        +------------------+      +--------------+
        | Puppet: Enforcer |      |              |
        |                  <------+   TEA4CUPS   |
        |    [Whiteout]    |      |              |
        +----+----------+--+      +--------------+
             |          |
             |          |
    +--------v-+      +-v---------+
    | Pre Hook |      | Post Hook |
    +--------+-+      +-+---------+
             |          |
           +-v----------v-+
           |              |
           | Redis Server |
           |              |
           +------+-------+
                  |
                  |
                  |
           +------v-------+       +--------------+
           |              +------->              |
           |   main.py    |       |  Print List  |
           |              <-------+              |
           +--------------+       +--------------+

### Useful Tips

Useful links: https://github.com/ocf/labmap/blob/master/Dockerfile

Useful command: `sudo docker run -d -it -p 8000:8000 --name printlist-gunicorn print-disp`
