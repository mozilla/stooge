This is Stooge. Work in progress.

Run Book
--------

*requirements*
* rabbitmq
* mongodb
* memcache

*installation*
...

*start*

```bash
$ cd /home/stooge

$ tmux
$ source env/bin/activate && ~/moz-stooge/scripts/stooge-scanner
$ source env/bin/activate && ~/moz-stooge/scripts/stooge-web -p 9090 -c /home/stooge/stooge.cfg
```

*adding new sites*

```
$ mongo stooge
$ db.sites.insert({owner:"yourorg",type:"production",url:"http://www.example.com"})
```
