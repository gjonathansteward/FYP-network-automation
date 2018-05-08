# FYP-network-automation
Repository including the python code developed during the duration of my final year project.
This project is a personal development while during my final year within university with Staffordshire University!
Follow the guys in my department here on twitter, they are some fantastic teachers! https://twitter.com/StaffsNetworks

This project implemented 3 main pieces of automation
1 - Removal of pyhsical interfaces from aggregate interfaces triggered either via the CLI/SYSLOG
2 - Detection of high utilisation and then routing change applied, triggered either via a cron job or CLI
3 - Automatic configuration of BGP peers based on existing details in a database, triggered either via a cron job or CLI

For understanding the code, please see the functional diagrams in the root directories
For my personal ramble about the code and a bit of a demo see: https://www.youtube.com/watch?v=ewrA6Ya7jjY&list=PL0QwH3WQmr-63QTi37YcLJ1qjdtgZSIHf




NOTE
======

To fully run this system you need a database running in the background
I am not a programmer by trade so the code isn't perfect!
Also I'm a git hub noob so if you suggest things I might just reach out and ask how to accept them.

\Note
======


Known issues:
When running the Syslog monitor and putting links back into lag with Cisco the syslog monitor removes the interface again due to syslog messages

Possible improvements:
Quicker turn around on the config lock
Graphical Front end
More automation
addtional details for bgp such as import and export policies.
tidier coding



