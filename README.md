# REDNIGHT

Cycle GitLab header logos over a duration of time and then reset to the default.
Perfect for cycling through increasingly angry pictures of your boss before a deadline!

1. Place images (png only, but it's an easy mod) to cycle through (in alphabetical order) in `imgs/`
1. Set credentials in `config.yml`
1. Launch with `./REDNIGHT.py BEGIN END` where BEGIN and END are epoch times (begin time may also be `now`)

### Example

To cycle through the eight sample images, one per hour, launch with `./REDNIGHT.py now $(date -v+8H +'%s')`
